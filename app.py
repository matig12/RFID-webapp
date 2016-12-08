from flask import Flask, render_template, json, request,redirect,session,jsonify
from flask.ext.mysql import MySQL
from threading import Thread
import rfid_db_server

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'why would I tell you my secret key?'

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'toor'
app.config['MYSQL_DATABASE_DB'] = 'rfid'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

def database_contains(uid):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute('select * from rfid.users where user_card_uid = "{}"'.format(uid))
    result = cursor.fetchall()
    conn.close()
    return len(result) > 0

@app.route('/')
def main():
    return redirect('showSignin')

@app.route('/showAddCard')
def showAddCard():
    return render_template('addCard.html')

@app.route('/showSignin')
def showSignin():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('signin.html')

@app.route('/userHome')
def userHome():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('error.html',error = 'Unauthorized Access')


@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')

@app.route('/deleteCard',methods=['POST'])
def deleteCard():
    try:
        if session.get('user'):
            id = request.form['id']

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rfid.users WHERE user_id = {}"
                           .format(id))
            result = cursor.fetchall()

            if len(result) is 0:
                conn.commit()
                return json.dumps({'status':'OK'})
            else:
                return json.dumps({'status':'An Error occured'})
        else:
            return render_template('error.html',error = 'Unauthorized Access')
    except Exception as e:
        return json.dumps({'status':str(e)})
    finally:
        cursor.close()
        conn.close()


@app.route('/getCardById',methods=['POST'])
def getCardById():
    try:
        if session.get('user'):
            
            _id = request.form['id']
            _user = session.get('user')
    
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_GetCardById',(_id,_user))
            result = cursor.fetchall()

            Card = []
            Card.append({'Id':result[0][0],'Title':result[0][1],'Description':result[0][2]})

            return json.dumps(Card)
        else:
            return render_template('error.html', error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html',error = str(e))

@app.route('/getCard')
def getCard():
    try:
        if session.get('user'):
            con = mysql.connect()
            cursor = con.cursor()
            cursor.execute('SELECT * FROM rfid.users')
            Cardes = cursor.fetchall()

            Cards_dict = []
            for Card in Cardes:
                Card_dict = {
                        'Id': Card[0],
                        'Name': Card[1],
                        'Surname': Card[2],
                        'UID': Card[3],
                        'Date': Card[4]}
                Cards_dict.append(Card_dict)

            return json.dumps(Cards_dict)
        else:
            return render_template('error.html', error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error = str(e))

@app.route('/addCard',methods=['POST'])
def addCard():
    try:
        if session.get('user'):
            userName = request.form['name']
            userSurname = request.form['surname']
            cardUID = request.form['cardUID']

            conn = mysql.connect()
            cursor = conn.cursor()
            # cursor.callproc('sp_addCard',(_title,_description,_user))
            cursor.execute(
                "INSERT INTO `rfid`.`users` (`user_name`, `user_surname`, `user_card_uid`) VALUES ('{}', '{}', '{}')"
                    .format(userName, userSurname, cardUID))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return redirect('/userHome')
            else:
                return render_template('error.html',error = 'An error occurred!')

        else:
            return render_template('error.html',error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html',error = str(e))
    finally:
        cursor.close()
        conn.close()


@app.route('/validateLogin',methods=['POST'])
def validateLogin():
        _username = request.form['login']
        _password = request.form['password']

        if _username == 'admin' and _password == 'toor':
            session['user'] = _username
            return redirect('/userHome')
        else:
            return render_template('error.html', error='Wrong Email address or Password.')


if __name__ == "__main__":
    Thread(target=rfid_db_server.start, daemon=True).start()
    app.run(port=5000)

