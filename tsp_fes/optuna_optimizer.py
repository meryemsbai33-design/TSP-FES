def optimiser_avec_optuna(matrice, n_trials=15):
    try:
        import optuna
    except ImportError as exc:
        raise RuntimeError("Optuna absent. Installez-le avec : pip install optuna") from exc
    from .genetique import algorithme_genetique
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objectif(trial):
        p = {
            "taille_population": trial.suggest_categorical("taille_population", [50, 100, 500]),
            "selection": trial.suggest_categorical("selection", ["RO", "Tournoi"]),
            "taux_mutation": trial.suggest_categorical("taux_mutation", [.2, .5, .8]),
            "taux_croisement": trial.suggest_categorical("taux_croisement", [.2, .5, .8]),
            "generations": trial.suggest_categorical("generations", [100, 500, 1000])
        }
        # Limitation à 120 générations par essai pour maîtriser la durée du tuning.
        _, score, _ = algorithme_genetique(
            matrice, p["taille_population"], p["selection"], p["taux_mutation"],
            p["taux_croisement"], min(p["generations"], 120), seed=trial.number+31)
        return score

    study = optuna.create_study(direction="minimize")
    study.optimize(objectif, n_trials=n_trials)
    return study.best_params, study.best_value
