# run.py

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    #app.run(host='0.0.0.0', debug=True)
    app.run(debug=True)
    #socketio.run(app, debug=True, host='0.0.0.0')