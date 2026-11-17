import random

def distance_tour(ordre, matrice):
    return sum(matrice[ordre[i]][ordre[(i+1) % len(ordre)]] for i in range(len(ordre)))

def selection_roulette(population, scores):
    poids = [1/max(s, 1e-9) for s in scores]
    return random.choices(population, weights=poids, k=1)[0][:]

def selection_tournoi(population, scores, taille=4):
    candidats = random.sample(range(len(population)), min(taille, len(population)))
    return population[min(candidats, key=lambda i: scores[i])][:]

def croisement_ox(p1, p2):
    """Order Crossover ; la position 0 reste réservée au dépôt."""
    n = len(p1)
    a, b = sorted(random.sample(range(1, n), 2))
    enfant = [-1]*n
    enfant[0] = 0
    enfant[a:b] = p1[a:b]
    genes = [g for g in p2[1:] if g not in enfant]
    places = [i for i in range(1, n) if enfant[i] == -1]
    for pos, gene in zip(places, genes):
        enfant[pos] = gene
    return enfant

def mutation_inversion(ch):
    enfant = ch[:]
    a, b = sorted(random.sample(range(1, len(ch)), 2))
    enfant[a:b+1] = reversed(enfant[a:b+1])
    return enfant

def algorithme_genetique(matrice, taille_population=100, selection="Tournoi",
                         taux_mutation=.2, taux_croisement=.8, generations=500,
                         callback=None, seed=None):
    if seed is not None:
        random.seed(seed)
    n = len(matrice)
    population = [[0] + random.sample(range(1, n), n-1) for _ in range(taille_population)]
    meilleur, meilleur_score = None, float("inf")
    historique = []
    for gen in range(generations):
        scores = [distance_tour(ch, matrice) for ch in population]
        idx = min(range(len(scores)), key=scores.__getitem__)
        if scores[idx] < meilleur_score:
            meilleur, meilleur_score = population[idx][:], scores[idx]
        historique.append(meilleur_score)
        nouvelle = [meilleur[:]]  # élitisme
        while len(nouvelle) < taille_population:
            select = selection_roulette if selection == "RO" else selection_tournoi
            p1, p2 = select(population, scores), select(population, scores)
            enfant = croisement_ox(p1, p2) if random.random() < taux_croisement else p1[:]
            if random.random() < taux_mutation:
                enfant = mutation_inversion(enfant)
            nouvelle.append(enfant)
        population = nouvelle
        if callback:
            callback(gen+1, generations)
    return meilleur, meilleur_score, historique
