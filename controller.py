from attributedict.collections import AttributeDict
import json
import scripts.run_match_internal
tactic_dict = {}
with open("tactics.json") as tactics:
    tactic_dict = AttributeDict(json.load(tactics))

#C:\\Users\\TheDonut\\Documents\\Berkeley\\terminal\\C1GamesStarterKit\\replays\\p1-22-05-2020-22-08-54-1590210534080--814654162.replay
def get_events(replay):
    jsonList = []
    with open(replay) as f:
        for jsonObj in f.readlines():
            if jsonObj.strip():
                j = json.loads(jsonObj)
                jsonList.append(j)
    return jsonList

def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
defense = tactic_dict.tactics.defense
defenses = [defense[i] for i in defense]
attack = tactic_dict.tactics.attack
attacks  = [attack[i] for i in attack]
attack = {i: attack[i] for i in attack if i in ["2", "3", "4", "5"]}
rounds_to_go = 120
cohesion = 20
genes = rounds_to_go // cohesion
tactic_attacks = {
int(i) - 1: [{} for j in range(rounds_to_go)] for i in attack
}
tactic_defenses = {
int(i) - 1: [{} for j in range(rounds_to_go)] for i in attack
}
def process(inp):
    count = 0
    output = []
    while count < len(inp):
        points = inp[count]
        points_next = inp[count + 1] if count + 1 != len(inp) else []
        if len(points) == 2 and len(points_next) != 1:
            output.append(points)
        if len(points_next) == 1:
            for i in points:
                output.append([i, points_next[0]])
        if points == "mirror":
            count_inner = count - 1
            if len(inp[count_inner]) == 2:
                while count_inner >= 0:
                    p = inp[count_inner]
                    output.append([14 + (13 - p[0]), p[1]])
                    count_inner -= 1
            else:
                for i in inp[count_inner - 1]:
                    output.append([13 + (13 - i), inp[count_inner][0]])
        count += 1
    return output

def tactic_defense_generate(tactic):
    defense_tactic = defenses[tactic]
    for i in range(rounds_to_go):
        for unit in ['FILTER', 'DESTRUCTOR', 'ENCRYPTOR']:
            points = []
            movement = defense_tactic[unit]["movement"]
            others = defense_tactic[unit]["points"]
            count = i
            while count >= 0:
                if str(count) in movement:
                    tactic_defenses[tactic][i][unit] = process(movement[str(count)])
                    break
                count -= 1
            count = i
            while count >= 0:
                if str(count) in others:
                    tactic_defenses[tactic][i][unit] = process(others[str(count)])
                    break
                count -= 1

def tactic_attack_generate(tactic):
    attack_tactic = attacks[tactic]
    print(tactic)
    for i in range(rounds_to_go):
        for unit in ['EMP', 'PING', 'SCRAMBLER']:
            positions = []
            amounts = []
            if "positions" in attack_tactic[unit]:
                positions = attack_tactic[unit]["positions"]
                keys = list(positions.keys())
                amounts = attack_tactic[unit]["amounts"]
                if positions == []:
                    continue
                else:
                    for i in positions:
                        if i != "end":
                            tactic_attacks[tactic][int(i)][unit] = [positions[i], amounts[i]]
                        else:
                            if positions[i] != "stop":
                                _,num = positions[i].split()
                                num = int(num)
                                pattern = list(map(int, keys[(-1 - num):-1]))
                                pattern = [0] + pattern if num == len(positions) - 1 else [int(keys[-2 - num])] + pattern
                                increments = [pattern[i] - pattern[i - 1] for i in range(1, len(pattern))]
                                pattern = pattern[1:]
                                count = 0
                                increment = pattern[-1]
                                while increment < rounds_to_go:
                                    increment += increments[count % len(pattern)]
                                    if increment >= rounds_to_go:
                                        break
                                    i = pattern[count % len(pattern)]
                                    tactic_attacks[tactic][int(increment)][unit] = [positions[str(i)], amounts[str(i)]]
                                    count += 1

for i in attack:
    tactic_attack_generate(int(i) - 1)
    tactic_defense_generate(int(i) - 1)

def pick_attacks(time):
    return time

def score(events, i, enemy):
    return sum([entry[1] for entry in events[i]['events']['breach'] if entry[-1] == enemy])

def reward(current, previous):
    return (score(current) - score(previous)) + (current.scored_on - previous.scored_on)

import numpy as np
def generate_chromosome(cohesion, tactic=-1):
    chromosome = [{"attack": {}, "defense": {}} for i in range(rounds_to_go)]
    if tactic == -1:
        choices = [np.random.choice(list(tactic_attacks.keys())) for _ in range(rounds_to_go // cohesion)]
    else:
        choices = [list(tactic_attacks.keys())[tactic] for _ in range(rounds_to_go // cohesion)]
    for i in range(rounds_to_go):
        chromosome[i]["attack"] = tactic_attacks[choices[i // cohesion]][i]
        chromosome[i]["defense"] = tactic_defenses[choices[i // cohesion]][i]
    return chromosome, choices

def get_chromosome_from_genes(genes):
    ret = [{"attack": [], "defense": []} for _ in range(rounds_to_go)]
    for i in range(len(genes)):
        for j in range(i * cohesion, i * cohesion + cohesion):
            ret[j]["attack"] = tactic_attacks[genes[i]][j]
            ret[j]["defense"] = tactic_defenses[genes[i]][j]
    return ret

# chromosomes = [generate_chromosome(cohesion) for _ in range(50)]
base_chromosomes = [generate_chromosome(cohesion, i) for i in range(len(attack))]

weights_attacks = {int(i) - 1: [100 for j in range(rounds_to_go)] for i in attack}
weights_defenses = {int(i) - 1: [100 for j in range(rounds_to_go)] for i in attack}

def fitness(replays):
    replay = get_events("replays\\" + replays)
    end = replay[-1]['endStats']
    Ma = end['player1']['points_scored']
    Ms = end['player2']['points_scored']
    b = 0.6
    Ct = replay[-1]['endStats']['turns']
    Cmax = 100
    self_destructs = 0
    for re in replay:
        if 'events' in re:
            for dest in re['events']['selfDestruct']:
                if dest[-1] == 1:
                    self_destructs += 1
    if end['winner'] == 1:
        return max(Ma / ((self_destructs + 1) * (Ma + Ms)), b)
    else:
        return min((Ct * Ma) / ((self_destructs + 1) * (Cmax * Ma + Cmax * Ms)), b)
import os


# def run_match_fitness(chromosome_in):
#      threads = []
#
#      t = Thread(target=)
#      threads.append(t)
#
#      ...repeat as often as necessary...
#
#      # Start all threads
#      for x in threads:
#          x.start()
#
#      # Wait for all of them to finish
#      for x in threads:
#          x.join()
res = []
for num, chromosome in enumerate(base_chromosomes):
    with open("adaptivestrat/config.json", "w") as f:
        json.dump(chromosome[0], f)
    scripts.run_match_internal.runner("adaptivestrat", "staticstrat")
    f = fitness(os.listdir("replays")[-1])
    res.append(get_events("replays\\" + os.listdir("replays")[-1]))
    print("tactic {} has fitness {}".format(tactic_dict.names[str(num + 1)], f))

def size_k_select(k):
    # chromosomes_tourney = [i for i in range(len(chromosomes))]
    chromosomes_scores = []
    replays = []
    tried = [[]]
    best = []
    chromosome = [[], []]
    for i in range(k):
        f = 0.0
        while f < 0.5:
            while chromosome[1] in tried:
                chromosome = generate_chromosome(cohesion)
            with open("adaptivestrat/config.json", "w") as f:
                json.dump(chromosome[0], f)
            scripts.run_match_internal.runner("adaptivestrat", "staticstrat")
            f = fitness(os.listdir("replays")[-1])
            print("fitness: {}".format(f))
            tried.append(chromosome[1])
            if f >= 0.5:
                replays.append(get_events("replays\\" + os.listdir("replays")[-1]))
                chromosomes_scores.append(f)
                best.append((chromosome, f))
            print(len(best))
    return replays, best, tried

import time
start = time.time()
replays_all, best_all, tried = size_k_select(2)
taken = time.time() - start
print(taken)
goal = 0.9
max_num = 200
chromosomes = best_all

def size_k_tourney(k):
    p = 0.9
    probs = np.array([p * (1-p) ** i for i in range(k)])
    choices = np.random.choice([i for i in range(len(chromosomes))], k)
    choices = sorted(choices, key=lambda x: -chromosomes[x][1])
    return chromosomes[np.random.choice(choices, p=probs / sum(probs))]

print("here")

while len(chromosomes) < max_num:
    chrom1, chrom2 = size_k_tourney(3), size_k_tourney(3)
    gene1, gene2 = chrom1[0][1], chrom2[0][1]
    fitness1, fitness2 = chrom1[1], chrom2[1]
    selector = np.random.random()
    if selector < 0.1:
        print("random")
        f = 0
        chromosome = generate_chromosome(cohesion)
        while f == 0:
            while chromosome[0][1] in tried:
                chromosome = generate_chromosome(cohesion)
            with open("adaptivestrat/config.json", "w") as f:
                json.dump(chromosome[0], f)
            scripts.run_match_internal.runner("adaptivestrat", "staticstrat")
            f = fitness(os.listdir("replays")[-1])
            tried.append(chromosome[1])
        chromosomes.append((chromosome, f))
        continue
    if selector < 0.55:
        ret_gene = []
        for i in range(len(gene1)):
            if np.random.random() < fitness1 / (fitness1 + fitness2):
                ret_gene.append(gene1[i])
            else:
                ret_gene.append(gene2[i])
    else:
        ret_gene = []
        if np.random.random() < fitness1 / (fitness1 + fitness2):
            ret_gene = list(gene1)
            for i in range(len(ret_gene)):
                if np.random.random() < fitness2 / (fitness1 + fitness2):
                    ret_gene[i] = gene2[i]
        else:
            ret_gene = list(gene2)
            for i in range(len(ret_gene)):
                if np.random.random() < fitness1 / (fitness1 + fitness2):
                    ret_gene[i] = gene1[i]
    chromosome = (get_chromosome_from_genes(ret_gene), ret_gene)
    with open("adaptivestrat/config.json", "w") as f:
        json.dump(chromosome[0], f)
    scripts.run_match_internal.runner("adaptivestrat", "staticstrat")
    f = fitness(os.listdir("replays")[-1])
    print("chromie")
    print(len(chromosomes))
    chromosomes.append((chromosome, f))
    if f > goal:
        break

best = max(chromosomes, key=lambda x: x[1])
with open("adaptivestrat/config.json", "w") as f:
    json.dump(best[0][0], f)

scripts.run_match_internal.runner("adaptivestrat", "staticstrat")
