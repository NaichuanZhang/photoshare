import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login

#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '112358'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass


#This will get all the album_name from albums talbe
def getAlbumList():
    cursor = conn.cursor()
    cursor.execute("SELECT album_name from Albums")
    return cursor.fetchall()

def getAlbumid(album_name_input):
    cursor = conn.cursor()
    cursor.execute("SELECT album_id FROM Albums WHERE album_name ='"+ album_name_input+"'")
    return cursor.fetchone()[0]
#get all the comment for one particular picture
def getComments():
    cursor = conn.cursor()
    cursor.execute("SELECT photo_id, description FROM Comments")
    return cursor.fetchall()
#get comments for particular picture
def getPicComments(picture_id):
    cursor = conn.cursor()
    cursor.execute("SELECT photo_id, description FROM Comments WHERE photo_id ='"+picture_id+"'")
    return cursor.fetchall()
@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/add_friend', methods = ['GET', 'POST'])
def addfriend():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		print uid
		email = request.form.get('friend_email')
		if isEmailExist(email):
			friendid = getUserIdFromEmail(email)
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Friends (friend_id_1, friend_id_2) VALUES ('{0}', '{1}')".format(uid, friendid))
			conn.commit()
			return render_template('hello.html', message="You added a new friend")
		else:
			return render_template('hello.html', message="Your friend is not found in the database")
	else:
		print "hello"
		return render_template('add_friend.html')

@app.route('/friend_show/<user_id>', methods = ['GET'])
@flask_login.login_required
def friend_show(user_id):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT friend_id_2 from Friends where friend_id_1='{0}'".format(uid))
	friends = cursor.fetchall()
	return render_template('friend_show.html', friends = friends)

@app.route('/show', methods = ['GET'])
@flask_login.login_required
def show():
    if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		photos=getPicturesid(uid)
		print photos
		return render_template('hello.html', name=flask_login.current_user.id, message='Here are your photos', photos=getUsersPhotos(uid), comments= getComments())
	#The method is GET so we return a  HTML form to upload the a photo.
    #TODO: show page in the hello template

@app.route('/comment_show/<picture_id>', methods=['GET'])
@flask_login.login_required
def comment_show(picture_id):
	print picture_id # log the picture_id
    	if request.method == 'GET':
			uid = getUserIdFromEmail(flask_login.current_user.id)
			comment = getPicComments(picture_id)
			print comment  #will show in the shell
			return render_template('comment_show.html', photos=getUsersPhotos(uid), comments= comment)




@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print cursor.execute("INSERT INTO Users (email, password) VALUES ('{0}', '{1}')".format(email, password))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]
def getPicturesid(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT picture_id FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code
def isEmailExist(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return True
	else:
		return False
#to check if user exist to add friends.

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/comment_new/<picture_id>', methods=['GET','POST'])
@flask_login.login_required
def comment_new(picture_id):
	print picture_id # log the picture_id
    	if request.method == 'POST':
			uid = getUserIdFromEmail(flask_login.current_user.id)
			comment = request.form.get('description')
			print comment  #will show in the shell
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Comments (description, photo_id) VALUES ('{0}', '{1}')".format(comment,picture_id))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message='Comment created!', photos=getUsersPhotos(uid))
	return render_template('comment_new.html',pid = picture_id)



@app.route('/albums_create', methods=['GET','POST'])
@flask_login.login_required
def album_create():
    	if request.method == 'POST':
    		uid = getUserIdFromEmail(flask_login.current_user.id)
    		album_name = request.form.get('album_name')
    		print album_name  #will show in the shell
    		cursor = conn.cursor()
    		cursor.execute("INSERT INTO Albums (album_name, owner_id) VALUES ('{0}', '{1}')".format(album_name,uid))
    		conn.commit()
    		return render_template('hello.html', name=flask_login.current_user.id, message='Album created!', photos=getUsersPhotos(uid))
    	#The method is GET so we return a  HTML form to upload the a photo.
    	else:
    		return render_template('albums_create.html')



@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
 	      	print caption
	       	album_name = request.form.get('album_name')
		print album_name
	       	aid = getAlbumid(album_name)
		print aid
	       	photo_data = base64.standard_b64encode(imgfile.read())
 	        cursor = conn.cursor()
 	        cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(photo_data,uid, caption, aid))
 	      	conn.commit()
	        return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid))
	else:
		return render_template('upload.html')

def getAllphotos():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures")
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#TODO:add create_tag
@app.route('/tag_new', methods =['GET','POST'])
def tag_new():
	if request.method == 'POST':
		tag_description = request.form.get('description')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Tags (description) VALUES ('{0}')".format(tag_description))
		conn.commit()
		return render_template('hello.html', message='Tag created')
	else:
		return render_template('tag_new.html')

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html',message='Welecome to Photoshare', photos = getAllphotos())


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
