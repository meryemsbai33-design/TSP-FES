import os, threading, webbrowser, math
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .donnees import construire_points
from .osrm import obtenir_matrice_osrm, matrice_estimee, obtenir_route_osrm
from .genetique import algorithme_genetique
from .optuna_optimizer import optimiser_avec_optuna
from .agents import agent_web, agent_scholar, agent_raisonneur
from .carte import creer_carte

class ApplicationTSP:
    def __init__(self, root):
        self.root=root
        root.title("TSP FES — Algorithme génétique, 40 points")
        root.geometry("1450x900")
        self.points=construire_points()
        self.matrice=None
        self.chemin_carte=None
        self._construire()

    def _construire(self):
        cadre=ttk.Frame(self.root,padding=8); cadre.pack(fill="both",expand=True)
        cadre.columnconfigure((0,1),weight=1); cadre.rowconfigure((0,1),weight=1)

        # Quadrant 1 : paramètres et modes.
        q1=ttk.LabelFrame(cadre,text="QUADRANT 1 — Définition et paramètres",padding=8)
        q1.grid(row=0,column=0,sticky="nsew",padx=5,pady=5)
        ttk.Label(q1,text="Ville : Fès     |     Nombre de points : 40").grid(row=0,column=0,columnspan=2,sticky="w")
        self.vars={
            "taille_population":tk.StringVar(value="100"), "selection":tk.StringVar(value="Tournoi"),
            "taux_mutation":tk.StringVar(value="0.2"), "taux_croisement":tk.StringVar(value="0.8"),
            "generations":tk.StringVar(value="500")}
        opts=[("Topsize","taille_population",["50","100","500"]),
              ("Sélection","selection",["RO","Tournoi"]),
              ("Taux de mutation","taux_mutation",["0.2","0.5","0.8"]),
              ("Taux de croisement","taux_croisement",["0.2","0.5","0.8"]),
              ("Nombre de cycles","generations",["100","500","1000"])]
        for row,(label,key,values) in enumerate(opts,1):
            ttk.Label(q1,text=label).grid(row=row,column=0,sticky="w",pady=2)
            ttk.Combobox(q1,textvariable=self.vars[key],values=values,state="readonly",width=15).grid(row=row,column=1,sticky="w")
        bar=ttk.Frame(q1); bar.grid(row=6,column=0,columnspan=2,sticky="w",pady=5)
        ttk.Button(bar,text="B1 — Manuel / Lancer",command=self.manuel).pack(side="left",padx=2)
        ttk.Button(bar,text="B2 — Optuna",command=self.optuna).pack(side="left",padx=2)
        ttk.Button(bar,text="B3 — IA agentique",command=self.agents).pack(side="left",padx=2)
        self.progress=ttk.Progressbar(q1,maximum=100); self.progress.grid(row=7,column=0,columnspan=2,sticky="ew",pady=4)
        self.status=ttk.Label(q1,text="Prêt."); self.status.grid(row=8,column=0,columnspan=2,sticky="w")
        self.log=tk.Text(q1,height=6,wrap="word",font=("Arial",8)); self.log.grid(row=9,column=0,columnspan=2,sticky="nsew")
        q1.rowconfigure(9,weight=1); q1.columnconfigure(1,weight=1)

        # Quadrant 2 : convergence et solution.
        q2=ttk.LabelFrame(cadre,text="QUADRANT 2 — Résultats",padding=8)
        q2.grid(row=0,column=1,sticky="nsew",padx=5,pady=5); q2.rowconfigure(0,weight=1); q2.columnconfigure(0,weight=1)
        self.fig=Figure(figsize=(5,2.5),dpi=90); self.ax=self.fig.add_subplot(111)
        self.ax.set_title("Courbe de convergence"); self.ax.set_xlabel("Génération"); self.ax.set_ylabel("Distance (km)")
        self.cv=FigureCanvasTkAgg(self.fig,master=q2); self.cv.get_tk_widget().grid(row=0,column=0,sticky="nsew")
        self.dist=ttk.Label(q2,text="Distance totale : —",font=("Arial",11,"bold")); self.dist.grid(row=1,column=0,sticky="w")
        self.chrom=tk.Text(q2,height=4,wrap="word"); self.chrom.grid(row=2,column=0,sticky="ew")

        # Quadrant 3 : représentation cartésienne.
        q3=ttk.LabelFrame(cadre,text="QUADRANT 3 — Plan cartésien du TSP",padding=8)
        q3.grid(row=1,column=0,sticky="nsew",padx=5,pady=5); q3.rowconfigure(0,weight=1); q3.columnconfigure(0,weight=1)
        self.figp=Figure(figsize=(5,3),dpi=90); self.axp=self.figp.add_subplot(111)
        self.cvp=FigureCanvasTkAgg(self.figp,master=q3); self.cvp.get_tk_widget().grid(row=0,column=0,sticky="nsew")
        self._dessiner_plan(None)

        # Quadrant 4 : carte Folium.
        q4=ttk.LabelFrame(cadre,text="QUADRANT 4 — Routage réel cartographié",padding=8)
        q4.grid(row=1,column=1,sticky="nsew",padx=5,pady=5)
        ttk.Label(q4,text="Carte interactive Folium (HTML) :").pack(anchor="w")
        self.mapinfo=ttk.Label(q4,text="Aucune carte générée."); self.mapinfo.pack(anchor="w",pady=5)
        ttk.Button(q4,text="Ouvrir la carte dans le navigateur",command=self.ouvrir_carte).pack(anchor="w")
        ttk.Label(q4,text="Quartiers : Fès el-Bali, Fès el-Jdid, Ville Nouvelle, Agdal,\n"
            "Narjiss, Atlas, Zouagha, Bensouda et Route d'Immouzer.").pack(anchor="w",pady=8)

    def ecrire(self,msg):
        self.log.insert("end",str(msg)+"\n"); self.log.see("end")

    def params(self):
        return {"taille_population":int(self.vars["taille_population"].get()),
                "selection":self.vars["selection"].get(),
                "taux_mutation":float(self.vars["taux_mutation"].get()),
                "taux_croisement":float(self.vars["taux_croisement"].get()),
                "generations":int(self.vars["generations"].get())}

    def appliquer_params(self,p):
        for k,v in p.items(): self.vars[k].set(str(v))

    def ui(self,fn,*args,**kwargs):
        self.root.after(0,lambda:fn(*args,**kwargs))

    def charger_matrice(self):
        if self.matrice is not None: return self.matrice,"OSRM" if self.mode_osrm else "Estimation"
        try:
            self.matrice=obtenir_matrice_osrm(self.points); self.mode_osrm=True
            mode="OSRM — distances routières"
        except Exception as exc:
            self.matrice=matrice_estimee(self.points); self.mode_osrm=False
            mode="Estimation géographique — OSRM indisponible"
            self.ui(self.ecrire,f"AVERTISSEMENT OSRM : {exc}. Distances estimées utilisées.")
        self.ui(self.ecrire,"Matrice calculée : "+mode)
        return self.matrice,mode

    def manuel(self): self.lancer(self.params())

    def optuna(self): threading.Thread(target=self.travail_optuna,daemon=True).start()
    def travail_optuna(self):
        try:
            self.ui(self.status.config,text="Optuna : optimisation des hyperparamètres…")
            matrice,mode=self.charger_matrice()
            self.ui(self.progress.configure,value=10)
            p,score=optimiser_avec_optuna(matrice,n_trials=15)
            self.ui(self.ecrire,f"Optuna — meilleurs paramètres : {p} ; score de calibration : {score:.2f} km")
            self.ui(self.appliquer_params,p)
            self.lancer(p,matrice,mode)
        except Exception as e:
            self.ui(messagebox.showerror,"Erreur Optuna",str(e))

    def agents(self): threading.Thread(target=self.travail_agents,daemon=True).start()
    def travail_agents(self):
        try:
            self.ui(self.status.config,text="Agents Web et Scholar en recherche…")
            self.ui(self.progress.configure,value=10)
            web=agent_web(); self.ui(self.ecrire,f"Agent Web ({web['source']}) : {web.get('texte','')[:450]}")
            self.ui(self.progress.configure,value=40)
            scholar=agent_scholar(); self.ui(self.ecrire,f"Agent Scholar ({scholar['source']}) : {scholar.get('articles',[])}")
            p,raison=agent_raisonneur(web,scholar)
            self.ui(self.ecrire,"Agent raisonneur : "+raison)
            self.ui(self.ecrire,"Paramètres arbitrés : "+str(p)); self.ui(self.appliquer_params,p)
            matrice,mode=self.charger_matrice()
            self.lancer(p,matrice,mode)
        except Exception as e: self.ui(messagebox.showerror,"Erreur agents",str(e))

    def lancer(self,p,matrice=None,mode=None):
        threading.Thread(target=self.travail_ga,args=(p,matrice,mode),daemon=True).start()

    def travail_ga(self,p,matrice,mode):
        try:
            self.ui(self.progress.configure,value=0); self.ui(self.status.config,text="Préparation des distances…")
            if matrice is None: matrice,mode=self.charger_matrice()
            self.ui(self.ecrire,f"GA lancé — {mode} — {p}")
            def avance(i,total):
                self.ui(self.progress.configure,value=100*i/total)
                if i==total or i%max(1,total//10)==0: self.ui(self.status.config,text=f"Génération {i}/{total}")
            ordre,score,hist=algorithme_genetique(matrice,p["taille_population"],p["selection"],
                p["taux_mutation"],p["taux_croisement"],p["generations"],callback=avance)
            geom=None; dist_route=None
            if self.mode_osrm:
                try: geom,dist_route=obtenir_route_osrm(self.points,ordre)
                except Exception as e: self.ui(self.ecrire,f"Géométrie OSRM non disponible : {e}")
            path=creer_carte(self.points,ordre,geometrie=geom)
            self.ordre,self.score,self.hist=ordre,score,hist
            self.chemin_carte=os.path.abspath(path)
            self.ui(self.afficher,ordre,score,hist,mode,dist_route,geom is not None)
            self.ui(self.progress.configure,value=100); self.ui(self.status.config,text="Calcul terminé.")
        except Exception as e:
            self.ui(messagebox.showerror,"Erreur d'exécution",str(e)); self.ui(self.status.config,text="Échec du calcul.")

    def afficher(self,ordre,score,hist,mode,dist_route,route_reelle):
        self.ax.clear(); self.ax.plot(range(1,len(hist)+1),hist)
        self.ax.set_title("Courbe de convergence"); self.ax.set_xlabel("Génération")
        self.ax.set_ylabel("Distance (km)"); self.ax.grid(True,alpha=.25); self.cv.draw()
        d=dist_route if dist_route is not None else score
        self.dist.config(text=f"Distance totale : {d:.2f} km — {mode}")
        self.chrom.delete("1.0","end")
        self.chrom.insert("end"," → ".join(self.points[i]["nom"] for i in ordre)+" → Entrepôt")
        self._dessiner_plan(ordre)
        self.mapinfo.config(text=self.chemin_carte+"\n"+("Tracé routier OSRM." if route_reelle else "Tracé estimé si OSRM indisponible."))

    def _dessiner_plan(self,ordre):
        self.axp.clear()
        lat0=sum(p["lat"] for p in self.points)/len(self.points)
        lon0=sum(p["lon"] for p in self.points)/len(self.points)
        xy=[((p["lon"]-lon0)*111.32*math.cos(math.radians(lat0)),
             (p["lat"]-lat0)*110.574) for p in self.points]
        for p,(x,y) in zip(self.points,xy):
            if p["depot"]:
                self.axp.scatter(x,y,marker="*",s=230,c="red",label="Entrepôt",zorder=4)
                self.axp.annotate("Dépôt",(x,y),xytext=(5,7),textcoords="offset points")
            else:
                self.axp.scatter(x,y,s=24,c="steelblue")
                self.axp.annotate(str(p["id"]),(x,y),xytext=(3,3),textcoords="offset points",fontsize=7)
        if ordre:
            route=[xy[i] for i in ordre]+[xy[ordre[0]]]
            self.axp.plot([v[0] for v in route],[v[1] for v in route],color="darkorange",lw=1.2)
        self.axp.set_title("Circuit TSP — projection locale")
        self.axp.set_xlabel("Est-Ouest (km)"); self.axp.set_ylabel("Nord-Sud (km)")
        self.axp.grid(True,alpha=.25); self.axp.legend(loc="best")
        self.figp.tight_layout(); self.cvp.draw()

    def ouvrir_carte(self):
        if self.chemin_carte and os.path.exists(self.chemin_carte):
            webbrowser.open("file://"+self.chemin_carte)
        else: messagebox.showinfo("Carte","Lancez d'abord un calcul.")

def lancer_interface():
    root=tk.Tk(); ApplicationTSP(root); root.mainloop()
