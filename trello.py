import requests
import sys
from json.decoder import JSONDecodeError


class EmptyInput(Exception):
    """
    Ошибка пустого инпута
    """
    pass


class NotFoundName(Exception):
    """
    Ощибка ненайденой задачи в колонки
    """
    pass


# данные авторизации  в trello api
auth_params = {
    'key': None,
    'token': None,
}
# адрес ,на котором расположен trello api,туда отправляем HTTP запросы
base_url = "https://api.trello.com/1/{}"
board_id = None


def read():
    """
    Вывод всех имеющихся данных на доске
    """
    # Получим данные всех колонок на доске:
    column_data = requests.get(base_url.format(
        'boards') + '/' + board_id + '/lists', params=auth_params).json()

    # Теперь выведем название каждой колонки и всех заданий, которые к ней относятся:
    for num_column, column in enumerate(column_data):
        print('_'*25)
        print(column['name'])
        # Получим данные всех задач в колонке и перечислим все названия
        task_data = requests.get(base_url.format(
            'lists') + '/' + column['id'] + '/cards', params=auth_params).json()
        if not task_data:
            print('\t' + 'Нет задач!')
            continue
        else:
            print('\t' + f'Всего задач: {len(task_data)}')
            for task in task_data:
                print('\t' + task['name']+'\t'+task['id'])


def create_column(column_name):
    """
    создание новой колонки
    """
    column_data = requests.get(base_url.format(
        'boards') + '/' + board_id + '/lists', params=auth_params).json()
    for column in column_data:
        if column['name'] == column_name:
            print("Колонка с таким названием уже существует")
            return
    response = requests.post(base_url.format(
        'lists'),  data={'name': column_name, 'idBoard': board_id, **auth_params}).json()
    return response


def column_check(column_name):
    """
    првоерка на существование колонки. Функция верент id колонки в случае успеха и None - в обратном случае
    """
    column_id = None
    column_data = requests.get(base_url.format(
        'boards') + '/' + board_id + '/lists', params=auth_params).json()
    for column in column_data:
        if column['name'] == column_name:
            column_id = column['id']
            return column_id


def create(name, column_name):
    """
    создание новой задачи в выбранной колонке
    """
    # Получим данные всех колонок на доске
    column_data = requests.get(base_url.format(
        'boards') + '/' + board_id + '/lists', params=auth_params).json()

    # Переберём данные обо всех колонках, пока не найдём ту колонку, которая нам нужна
    column_id = column_check(column_name)

    if column_id is None:
        column_id = create_column(column_name)['id']

    requests.post(base_url.format('cards'), data={
        'name': name, 'idList': column['id'], **auth_params})


def find_dublicated_tasks(task_name):
    """
    функция ,которая ищет  дубликаты  и помещает их в список
    """
    dublicate_tasks_list = []
    # получим данные колонок
    column_data = requests.get(base_url.format(
        'boards') + '/' + board_id + '/lists', params=auth_params).json()
    # проинтерируемся по колонкам ,получим данные задач и добавим дубликаты в dublicate_list
    for column in column_data:
        column_tasks = requests.get(base_url.format(
            'lists')+'/'+column['id']+'/cards', params=auth_params).json()
        for task in column_tasks:
            if task['name'] == task_name:
                dublicate_tasks_list.append(task)
    return dublicate_tasks_list


def move(task_name, column_name):
    """
    функция,реализующая функцию перемещения задач между колонок 
    и обработку случая возниковения дубликатов
    """
    task_id = None
    # Получим данные всех колонок на доске
    column_data = requests.get(base_url.format(
        'boards') + '/' + board_id + '/lists', params=auth_params).json()
    dublicate_tasks = find_dublicated_tasks(task_name)
    if len(dublicate_tasks) > 1:
        print("Присутствуют несколько дубликатов по вашему запросу")
        print("index | task-id | list-name")
        for index, task in enumerate(dublicate_tasks):
            # получим название колонки,в которой находится текущая задача
            task_column = requests.get(base_url.format(
                "lists")+'/'+task['idList'], params=auth_params).json()
            task_column_name = task_column['name']

            print(f"{index} | {task['id']} | {task_column_name}")
        task_id = input("Выберите задачу и впешите её ID: ")
    else:
        if dublicate_tasks[0]['id'] is None:
            raise NotFoundName
        task_id = dublicate_tasks[0]['id']
    # Теперь у нас есть id задачи, которую мы хотим переместить

    column_id = column_check(column_name)

    if column_id is None:
        column_id = create_column(column_name)['id']
    # И выполним запрос к API для перемещения задачи в нужную колонку
    requests.put(base_url.format('cards') + '/' + task_id +
                 '/idList', data={'value': column_id, **auth_params})
    print("Данные успешно обновлены")


if __name__ == "__main__":
    try:
        auth_params['key'] = input("Введите ваш trello-key: ")
        auth_params['token'] = input("Введите ваш trello-token: ")
        board_short_id = input(
            "Введите короткий id доски(посмотреть можно в url в браузере): ")
        if not (auth_params['key'] and auth_params['token'] and board_short_id):
            raise EmptyInput
        board_id = requests.get(base_url.format("boards") +
                                '/'+board_short_id, params=auth_params).json()['id']

        if len(sys.argv) <= 2:
            read()
        elif sys.argv[1] == 'create_column':
            create_column(sys.argv[2])
        elif sys.argv[1] == 'create':
            create(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == 'move':
            move(sys.argv[2], sys.argv[3])
    except EmptyInput:
        print('Введите хотя бы что-нибудь, пожалуйста...')
    except JSONDecodeError:
        print("Ошибка доступа к сервису")
    except NotFoundName:
        print("Введенное название задачи отсутствует в списках, попробуйте ввести снова")
