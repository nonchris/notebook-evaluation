import os
import json
import time
import traceback
from typing import Tuple

"""
A script for evaluating Jupyter Notebooks via terminal:
- finds all notebooks named 'Bericht_student_python.ipynb' in the current directory and sub-directories
- detects tasks and executes them successively
- it asks the evaluator to give points after executing a task
    - the executed code can be displayed on demand
    - the code of one task can also be saved to a file
- if the notebook was evaluated with enough points the code will continue with the next notebook automatically
- there results will be saved in a scv file (path to file and True / False for reaching required points)
    - path to file | total points | True/False | Points for each task
    
Note that there can be imports in the executed code that require external libraries

Written by Christoph Geron with some assistance of Lennart Nitsche
"""


def eval_dialogue(current_task: str, filename: str, full_code: str, points_as_csv_string: str, total_points: int) \
        -> Tuple[int, str]:
    """

    :param current_task: name of current task
    :param filename: name of current file
    :param full_code: full code of current task
    :param points_as_csv_string: string for csv table
    :param total_points: total points
    :returns: points_for_csv and points as number
    """
    # asking to display the code
    ip = input('Wanna see the code? 1 = yes, 2 = save to file, else: any ')
    if ip == '1':
        print()
        print(full_code)
        print()

    # saving code of task on demand
    elif ip == '2':
        save_name = f'task-{current_task.replace(" ", "-")[12:]}.py'
        # unique filename
        i = 1
        while os.path.isfile(save_name):
            save_name = f'task-{current_task.replace(" ", "-")[12:]}-{i}.py'
            i += 1

        # writing code
        with open(save_name, 'w') as sv:
            sv.write(f'# from: {filename}\n{full_code}')
        print(f'SAVED code under {save_name}')

    pts = input(f'Enter given points for {current_task} ')
    # just a check whether our tutor is alive or feel asleep on the enter key
    while not pts:
        print("WAKE UP!")
        time.sleep(1.5)
        pts = input(f'ENTER POINTS for {current_task} task! ')
    total_points += int(pts)
    points_as_csv_string += f'{pts};'
    return total_points, points_as_csv_string


def exec_notebook(filename="Bericht_tutor_python.ipynb", required_points=50) -> Tuple[bool, int, str]:
    # this is stupid but a way to show the plots
    # notebooks don't need a show command to sow the plot
    # this will be appended on every code line
    show_stuff = '''
try:
    ax.show()

except:
    try:
        plt.show()
    except:
        pass
    '''

    total_points = 0
    points_as_csv_string = ''  # used for csv writing
    # file_name = 'Bericht_student_python.ipynb'

    with open(filename, 'r') as f:
        output: dict = json.load(f)  # load notebook as json dict

        # iteration trough all cells
        current_task = ''  # holds current task name
        full_code = ''  # holds the whole code of one task -> all cells summed up
        for cell in output['cells']:
            t = cell['cell_type']

            # check for markdown cell to find task start
            if t == 'markdown':
                first_line: str = cell['source'][0]

                if cell['source'][0].startswith('## Übungsblatt'):
                    # asking for points for the current task before going to next one
                    if current_task:
                        total_points, points_as_csv_string = eval_dialogue(
                            current_task, filename, full_code,
                            points_as_csv_string, total_points)
                        full_code = ''  # clearing code from that task

                    # check if 50+ points are reached
                    # prints will happen after the loop
                    if total_points >= required_points:
                        return True, total_points, points_as_csv_string

                    # extracting headline - asking whether the code should go on
                    print(current_task := first_line[3:])
                    input('Press enter to continue ')
            # check for declaration that author did write his stuff alone
            if first_line.startswith('## Erklärung'):

                # summing cells content up
                declaration = ''
                for line in cell['source']:
                    declaration += line

                # asking if valid
                print(declaration)
                ip = input('Is ths a valid Selbständigkeitserklärung? yes = 1 ')
                if ip != '1':
                    print('Okay - breaking')
                    return False, total_points, points_as_csv_string

            # for executing codeblocks
            elif t == 'code':
                # lines in cell will be added before execution
                code = ''''''
                for line in cell['source']:
                    code += line

                print("----New-Cell-----")

                # getting rid of that inline statement
                # append show commands
                try:
                    exec(code.replace('%matplotlib inline', '' + show_stuff), locals(), locals())
                    print()

                except:
                    print(traceback.format_exc())
                    print(f'CODE for {current_task} FAILED')
                    # showing code if requested
                    ip = input('Wanna see the code of the failing cell? 1 = yes, else: any ')
                    if ip == '1':
                        print('\n')
                        print(code)

                finally:
                    # adding code from cell to string that holds full code of a task
                    full_code += code

    total_points, points_as_csv_string = eval_dialogue(current_task, filename, full_code,
                                                       points_as_csv_string, total_points)

    return (True, total_points, points_as_csv_string) if total_points >= required_points else (
        False, total_points, points_as_csv_string)


if __name__ == '__main__':
    # path to file to check
    # file_name = "Bericht_student_python.ipynb"

    file_name = 'Bericht_student_python.ipynb'
    needed_points = 50

    results_file = 'results.csv'  # file results for each file are written to

    # walking all directories to find all matching notebooks
    for folder in os.walk('.'):
        path = f'{folder[0]}/{file_name}'
        if os.path.exists(path):
            # entering execution process
            print(f'OPENING NOTEBOOK AT: {folder[0]}')
            status, total, points = exec_notebook(filename=path, required_points=needed_points)

            # conclusion for this file
            print()
            print(
                f'{file_name} has passed the test!\nwith {total} points' if total >= needed_points
                else f'{file_name} has failed with {total} points')
            print()

            # writing whether file contained enough points
            # path to file | total points | True/False | Points for each task
            with open(results_file, 'a') as f:
                f.write(f'{path};{total};{status};{points}\n')
