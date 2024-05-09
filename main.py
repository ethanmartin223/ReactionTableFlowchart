# -------------- # Imports # -------------- #
import requests
import csv
import graphviz
import os


# -------------- # Functions # -------------- #
def get_google_spreadsheet(url: str):
    file_id = url.split('/')[-2]
    dwn_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&id={file_id}&gid=0'
    return requests.get(dwn_url).content.decode().replace('\r\n', '\n')


def get_array_from_csv(filename):
    arr = []
    with open(filename, mode='r') as file:
        csv_file = csv.reader(file)
        for lines in csv_file:
            arr.append([x.strip() for x in lines])
    return arr


def get_react(reactant_1, reactant_2, array):
    column_position_reactant_1 = None
    row_position_reactant_1 = None

    column_position_reactant_2 = None
    row_position_reactant_2 = None

    for x in range(len(array[0])):
        if array[0][x] == reactant_1:
            column_position_reactant_1 = x
        if array[0][x] == reactant_2:
            column_position_reactant_2 = x

    for y in range(len(array)):
        if array[y][0] == reactant_1:
            row_position_reactant_1 = y
        if array[y][0] == reactant_2:
            row_position_reactant_2 = y
    reaction_1 = reaction_2 = ''
    if row_position_reactant_1 is not None and column_position_reactant_2 is not None:
        reaction_1 = array[row_position_reactant_1][column_position_reactant_2]
    if row_position_reactant_2 is not None and column_position_reactant_1 is not None:
        reaction_2 = array[row_position_reactant_2][column_position_reactant_1]
    return reaction_1 if reaction_1 != '' else reaction_2


def get_best_reactant(array, available_to_react, total_reactants):
    global no_reaction_symbol
    best_r = None
    reactions_dict = dict()
    best_react_score = float('-inf')
    temp = []

    for reactant in total_reactants:
        reactions_dict[reactant] = {}
        for i in available_to_react:
            if i == reactant:  # this may break some things that use N.R. and NR
                e = no_reaction_symbol
            else:
                e = get_react(reactant, i, array)

            try:
                reactions_dict[reactant][e].append(i)
            except KeyError:
                reactions_dict[reactant][e] = []
                reactions_dict[reactant][e].append(i)
        # print(reactant, reactions_dict[reactant])
        for a in reactions_dict[reactant]:
            try:
                if a[1] not in temp:
                    temp.append(a[1])
            except IndexError:
                raise ValueError(f"Unrecoverable Hole In Table at {reactant}+{a}")
        if len(temp) > best_react_score:
            best_react_score = len(temp)
            best_r = reactant
        temp.clear()
    return best_r, reactions_dict


def graph_react(array, schem, parent_node, parent_chemical, reaction_data, reactants):
    global total_endings

    c_name = int(parent_node)
    for i, v in enumerate(reaction_data[parent_chemical].keys()):
        c_name += 1
        observation_node_name = str(c_name)
        schem.node(str(c_name), str(v), shape='box')
        schem.edge(parent_node, str(c_name))

        have_already_calculated_next_reactant = False
        for j, c in enumerate(reaction_data[parent_chemical][v]):
            c_name += 1
            chemical_node_name = str(c_name)
            schem.node(str(c_name), str(c), shape='' if len(reaction_data[parent_chemical][v]) > 1 else 'doubleoctagon')
            schem.edge(observation_node_name, str(c_name))
            if len(reaction_data[parent_chemical][v]) == 1:
                total_endings += 1

            if len(reaction_data[parent_chemical][v]) > 1 and not have_already_calculated_next_reactant:
                b_react, data = get_best_reactant(array, reaction_data[parent_chemical][v], reactants)
                have_already_calculated_next_reactant = True
                c_name += 1
                next_reactant_to_test_name = str(c_name)

                schem.node(str(c_name), b_react)
                schem.edge(chemical_node_name, str(c_name), label='+')
                c_name += graph_react(array, schem, str(c_name), b_react, data, reactants)
            elif len(reaction_data[parent_chemical][v]) > 1 and have_already_calculated_next_reactant:
                schem.edge(str(c_name), next_reactant_to_test_name, label='+')
    return c_name


# -------------- # Main Program #----------------#
url = input("Google Sheets URL: ")

print(f"Fetching Data from {url}... ", end='')
csv_data = get_google_spreadsheet(url)
f = open('outputFiles/data.csv', 'w')
f.write(csv_data)
f.close()
print(f"Done")

print(f"Writing CSV from data... ", end='')
no_reaction_symbol = 'N.R.' if csv_data.find('N.R.') > -1 else 'NR'
array = get_array_from_csv('outputFiles/data.csv')
reactants = (array[0][1:])
# for y in range(1, len(array)-1):
#     if array[y][0] not in reactants:
#         reactants.append(array[y][0]) print(f"Done")

reactants = list(reactants)
total_endings = 0
best_reactant, reactions_data = get_best_reactant(array, reactants, reactants)

print(f"Starting GraphViz... ", end='')
os.environ["PATH"] = 'Graphviz-10.0.1-win64/bin'
f = graphviz.Graph(filename="out.gv", engine='dot', graph_attr={}, node_attr={}, format='pdf')
print(f"Done")

print(f"Generating Tree... ", end='')
current_node_name = 1
f.node('0', "Unknown Solution", shape='rect')
f.node(str(current_node_name), best_reactant)
f.edge('0', str(current_node_name), label='+')
graph_react(array, f, '1', best_reactant, reactions_data, reactants)
print(f"Done")

print(f"Rendering... ", end='')
f.render('output')
print(f"Done")

print(f"\nFinished Rendering with {len(reactants)} starting reactions and {total_endings} ending reactants\n")
f.render()
os.system('output.pdf')
