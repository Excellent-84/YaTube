## Социальная сеть Yatube

### Описание проекта:

Приложение с пользовательским интерфейсом. Реализована регистрация и аутентификация пользователей. Авторизованный пользователь может создать и отредактировать свои пост, добавить текст и фото, писать комментарии к постам и подписываться на страницы других пользователей. Посты могут быть привязаны к тематической группе. Доступны к просмотру:

 * список всех постов на главной странице
 * список постов конкретного автора
 * список постов определенной тематической группы
 * новостная лента авторизованного пользователя - посты от авторов из подписок

На каждую страницу выводится 10 последних постов, реализована пагинация. Список постов на главной странице сайта хранится в кэше и обновляется раз в 20 секунд.

Для всего проекта написаны тесты с помощью библиотеки Unittest.

``` 
YaTube/yatube/posts/tests/
```

### Стек технологий:
<img src="https://img.shields.io/badge/Python-FFFFFF?style=for-the-badge&logo=python&logoColor=3776AB"/><img src="https://img.shields.io/badge/django-FFFFFF?style=for-the-badge&logo=django&logoColor=082E08"/><img src="https://img.shields.io/badge/SQLite-FFFFFF?style=for-the-badge&logo=SQLite&logoColor=003B57"/><img src="https://img.shields.io/badge/Unittest-FFFFFF?style=for-the-badge&logo=&logoColor=361508"/>

### Как запустить проект:

##### Клонировать репозиторий и перейти в него в командной строке:

``` 
git clone https://github.com/Excellent-84/YaTube.git
```

##### Cоздать и активировать виртуальное окружение:

``` 
cd yatube
python3 -m venv venv
source venv/bin/activate
```

##### Установить зависимости из файла requirements.txt:

``` 
pip install -r requirements.txt
```

##### Создать файл .env и указать необходимые токены по примеру .env.example:
``` 
touch .env
```

##### Выполнить миграции:

```
cd yatube
python3 manage.py migrate
```

##### Запустить проект:

``` 
python3 manage.py runserver
```

#### Автор: [Горин Евгений](https://github.com/Excellent-84)
