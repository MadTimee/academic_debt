from app import create_app

app = create_app()

if __name__ == '__main__':
    # Запускаем приложение в режиме отладки
    app.run(debug=True)