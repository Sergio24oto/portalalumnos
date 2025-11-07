from portal import create_app

# Creamos una instancia de la aplicación.
app = create_app()

if __name__ == "__main__":
    # app.run() a
    app.run(debug=True)
