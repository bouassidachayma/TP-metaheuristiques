"""Cedule de maintenance de centrales electriques - algorithme genetique.

Selection par loterie (roulette), croisement a 1 point sur des blocs de 4 bits,
mutation par inversion (+ autres mutations a comparer).
"""
import itertools
import random

# ------------------------------------------------------------------ donnees
CAPACITE = [20, 15, 35, 40, 15, 15, 10]   # MW des unites 1..7
DUREE = [2, 2, 1, 1, 1, 1, 1]             # intervalles de maintenance requis
DEMANDE = [80, 90, 65, 70]                # MW demandes aux intervalles 1..4
NB_UNITES, NB_INTERVALLES = len(CAPACITE), len(DEMANDE)
CAP_TOTALE = sum(CAPACITE)                # 150 MW


def genes_possibles(duree):
    """Motifs de 4 bits valides : 'duree' intervalles consecutifs a 1."""
    return ["0" * s + "1" * duree + "0" * (NB_INTERVALLES - s - duree)
            for s in range(NB_INTERVALLES - duree + 1)]


GENES = [genes_possibles(d) for d in DUREE]
# unite 1, 2 : 1100, 0110, 0011 ; unites 3..7 : 1000, 0100, 0010, 0001


# ------------------------------------------------------ chromosome et fitness
def individu_aleatoire():
    return [random.choice(GENES[i]) for i in range(NB_UNITES)]


def valide(chrom):
    return all(chrom[i] in GENES[i] for i in range(NB_UNITES))


def reserves(chrom):
    """Reserve nette de chaque intervalle = capacite totale - puissance perdue - demande."""
    res = []
    for t in range(NB_INTERVALLES):
        perdue = sum(CAPACITE[i] for i in range(NB_UNITES) if chrom[i][t] == "1")
        res.append(CAP_TOTALE - perdue - DEMANDE[t])
    return res


def fitness(chrom):
    """Performance = plus petite reserve ; 0 si elle est negative."""
    return max(0, min(reserves(chrom)))


# ------------------------------------------------------------ operateurs
def selection_loterie(pop, fits):
    """Roulette : probabilite de choisir un individu = f_k / somme(f)."""
    total = sum(fits)
    if total == 0:                       # population sans individu realisable
        return random.choice(pop)
    r = random.uniform(0, total)
    cumul = 0
    for ind, f in zip(pop, fits):
        cumul += f
        if r <= cumul:
            return ind
    return pop[-1]


def croisement(p1, p2, pc):
    """Croisement a 1 point, uniquement entre deux genes (blocs de 4 bits)."""
    if random.random() < pc:
        k = random.randint(1, NB_UNITES - 1)
        return p1[:k] + p2[k:], p2[:k] + p1[k:]
    return p1[:], p2[:]


def mutation_inversion(chrom):
    """Inversion : dans un segment de genes consecutifs, on inverse l'ordre des
    4 bits de chaque bloc (la maintenance est 'miroir' dans le temps :
    1100 <-> 0011, 1000 <-> 0001, 0100 <-> 0010). Le resultat reste valide."""
    c = chrom[:]
    i = random.randint(0, NB_UNITES - 1)
    j = random.randint(i, NB_UNITES - 1)
    for k in range(i, j + 1):
        c[k] = c[k][::-1]
    return c


def mutation_inversion_ordre(chrom):
    """Inversion classique : on inverse l'ordre des genes d'un segment.
    Refusee (chromosome inchange) si le resultat n'est plus valide."""
    c = chrom[:]
    i, j = sorted(random.sample(range(NB_UNITES), 2))
    c[i:j + 1] = c[i:j + 1][::-1]
    return c if valide(c) else chrom[:]


def mutation_remplacement(chrom):
    """Un gene est remplace par un autre motif valide de la meme unite
    (exemple de mutation du cours : 0001 -> 0100)."""
    c = chrom[:]
    i = random.randrange(NB_UNITES)
    c[i] = random.choice([g for g in GENES[i] if g != c[i]])
    return c


def mutation_echange(chrom):
    """Echange des genes de deux unites de meme duree (resultat toujours valide)."""
    c = chrom[:]
    i = random.randrange(NB_UNITES)
    autres = [j for j in range(NB_UNITES) if j != i and DUREE[j] == DUREE[i]]
    j = random.choice(autres)
    c[i], c[j] = c[j], c[i]
    return c


def aucune_mutation(chrom):
    return chrom[:]


MUTATIONS = {
    "inversion (bits des blocs)": mutation_inversion,
    "inversion (ordre des genes)": mutation_inversion_ordre,
    "remplacement de gene": mutation_remplacement,
    "echange de genes": mutation_echange,
    "aucune mutation": aucune_mutation,
}


# --------------------------------------------------------- algorithme genetique
def algorithme_genetique(mutation=mutation_inversion, taille_pop=50, generations=50,
                         pc=0.8, pm=0.2, elite=1, seed=None, verbose=False):
    if seed is not None:
        random.seed(seed)
    pop = [individu_aleatoire() for _ in range(taille_pop)]
    meilleur, f_meilleur, gen_opt = None, -1, None
    for g in range(1, generations + 1):
        fits = [fitness(c) for c in pop]
        k = max(range(taille_pop), key=lambda i: fits[i])
        if fits[k] > f_meilleur:
            meilleur, f_meilleur, gen_opt = pop[k][:], fits[k], g
        if verbose and (g in (1, 2, 5, 10, 15, 20, 30, 50) or g == generations):
            print(f"Generation {g:2d} | meilleure = {fits[k]:2d} | moyenne = {sum(fits)/taille_pop:5.1f}"
                  f" | meilleur depuis = gen {gen_opt}")
        # elitisme : les meilleurs passent tels quels
        ordre = sorted(range(taille_pop), key=lambda i: fits[i], reverse=True)
        nouvelle = [pop[i][:] for i in ordre[:elite]]
        while len(nouvelle) < taille_pop:
            p1 = selection_loterie(pop, fits)
            p2 = selection_loterie(pop, fits)
            for e in croisement(p1, p2, pc):
                if random.random() < pm:
                    e = mutation(e)
                nouvelle.append(e)
        pop = nouvelle[:taille_pop]
    fits = [fitness(c) for c in pop]
    k = max(range(taille_pop), key=lambda i: fits[i])
    if fits[k] > f_meilleur:
        meilleur, f_meilleur, gen_opt = pop[k][:], fits[k], generations
    return meilleur, f_meilleur, gen_opt


# ------------------------------------------------------------- verification
def optimum_exact():
    """Enumeration des 3 x 3 x 4^5 = 9216 chromosomes possibles."""
    return max((list(c) for c in itertools.product(*GENES)), key=fitness)


def afficher_cedule(chrom):
    print("Chromosome :", " ".join(chrom))
    res = reserves(chrom)
    for t in range(NB_INTERVALLES):
        unites = [i + 1 for i in range(NB_UNITES) if chrom[i][t] == "1"]
        perdue = sum(CAPACITE[i - 1] for i in unites)
        print(f"  Intervalle {t+1} : unites en maintenance {unites} | perdue = {perdue:2d} MW"
              f" | demande = {DEMANDE[t]} | reserve = {res[t]}")
    print("  Performance (plus petite reserve) =", fitness(chrom))


def comparer(taille_pop, generations, nb_runs, f_opt):
    """Compare les mutations sur nb_runs executions (graines 1..nb_runs)."""
    print(f"{'mutation':30s} | moyenne | min | optimum atteint | generation moyenne de l'optimum")
    for nom, mut in MUTATIONS.items():
        res = [algorithme_genetique(mutation=mut, taille_pop=taille_pop, generations=generations, seed=s)
               for s in range(1, nb_runs + 1)]
        fs = [r[1] for r in res]
        atteint = [r[2] for r in res if r[1] == f_opt]
        gen = f"{sum(atteint)/len(atteint):.1f}" if atteint else "-"
        print(f"{nom:30s} | {sum(fs)/nb_runs:7.2f} | {min(fs):3d} | {len(atteint):3d} / {nb_runs:<3d}      | {gen}")


if __name__ == "__main__":
    print("=== Verification avec le chromosome d'exemple du cours ===")
    exemple = ["0110", "0011", "0001", "1000", "0100", "0010", "1000"]
    print("valide :", valide(exemple), "| reserves :", reserves(exemple), "| performance :", fitness(exemple))

    print("\n=== Algorithme genetique (selection par loterie, mutation par inversion) ===")
    print("Parametres : population 50, 50 generations, pc = 0.8, pm = 0.2, elitisme = 1, graine 21")
    best, f, _ = algorithme_genetique(verbose=True, seed=21)
    afficher_cedule(best)

    opt = optimum_exact()
    f_opt = fitness(opt)
    nb_opt = sum(fitness(list(c)) == f_opt for c in itertools.product(*GENES))
    print("\n=== Optimum exact (enumeration de 9216 chromosomes) ===")
    afficher_cedule(opt)
    print(f"  Nombre de chromosomes optimaux : {nb_opt} / 9216")

    print("\n=== Comparaison des mutations : population 50, 50 generations, 30 executions ===")
    comparer(50, 50, 30, f_opt)

    print("\n=== Comparaison des mutations : population 10, 30 generations, 100 executions ===")
    comparer(10, 30, 100, f_opt)
