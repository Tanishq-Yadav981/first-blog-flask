from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from datetime import datetime
import json
from flask_mail import Mail
import os
import math
from werkzeug.utils import secure_filename

with open('config.json','r') as c:
	params = json.load(c)["params"]

local_server=True

app= Flask(__name__)
app.secret_key = 'super-secret-key'

app.config.update(

	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT='465',
	MAIL_USE_SSL=True,
	MAIL_USERNAME=params['gmail-user'],
	MAIL_PASSWORD=params['gmail-password']
)

mail=Mail(app)

if(local_server):
	app.config['SQLALCHEMY_DATABASE_URI']= params['local_uri']

else:
	app.config['SQLALCHEMY_DATABASE_URI']= params['prod_uri']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['UPLOAD_FOLDER']=params['upload_location']

db= SQLAlchemy(app)

class Contacts(db.Model):
	sno = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20), nullable=False)
	email = db.Column(db.String(40),nullable=False)
	phone = db.Column(db.String(20),nullable=False)
	message = db.Column(db.String(100),nullable=False)
	dateT = db.Column(db.String(40),nullable=True)

class Posts(db.Model):
	sno = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(30), nullable=False)
	tag_line = db.Column(db.String(50), nullable=False)
	slug = db.Column(db.String(25),nullable=False)
	content = db.Column(db.String(200),nullable=False)
	dateT = db.Column(db.String(40),nullable=True)
	pics_file = db.Column(db.String(12),nullable=False)

@app.route("/")

def home():

	posts=Posts.query.filter_by().all()
	last=math.ceil(len(posts)/int(params['no_of_post']))

	page=request.args.get('page')
	if(not str(page).isnumeric()):
		page=1

	page=int(page)
	print("Page:",page)

	posts=posts[(page-1)*int(params['no_of_post']):(page-1)*int(params['no_of_post'])+int(params['no_of_post'])]
	if(page==1):
		prevP="#"
		nextP="/?page="+str(page+1)

	elif(page==last):
		nextP="#"
		prevP="/?page="+str(page-1)

	else:
		prevP="/?page="+str(page-1)
		nextP="/?page="+str(page+1)

	
	return render_template('index.html',params=params,posts=posts,prevP=prevP,nextP=nextP)

@app.route("/about")

def about():

	return render_template('about.html',params=params)

@app.route("/dashboard",methods=['GET','POST'])

def dashboard():

	if ('user' in session and session['user']==params['admin_user']):
		posts=Posts.query.all()
		# print("post12")
		return render_template('dashboard.html',params=params,posts=posts)

	if request.method=='POST':
		username=request.form.get('Uemail')
		userpass=request.form.get('Upassword')
		if username==params['admin_user'] and userpass==params['admin_password']:
			# set the session variable
			session['user']=username
			posts=Posts.query.all()
			return render_template('dashboard.html',params=params,posts=posts)

	return render_template('login.html',params=params)

@app.route("/uploader",methods=['GET','POST'])

def uploader():

	if ('user' in session and session['user']==params['admin_user']):
		if(request.method=='POST'):
			f=request.files['file1']
			f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
			return "Uploaded Successfully"

@app.route("/logout")

def logout():
	session.pop('user')
	return redirect('/dashboard')

@app.route("/delete/<string:sno>",methods=['GET','POST'])

def delete(sno):
	if ('user' in session and session['user']==params['admin_user']):
		post=Posts.query.filter_by(sno=sno).first()
		db.session.delete(post)
		db.session.commit()
	return redirect('/dashboard')

@app.route("/contact",methods=['GET','POST'])

def contact():

	if(request.method=='POST'):
		'''Add entry'''
		name=request.form.get('name')
		email=request.form.get('email')
		phone=request.form.get('phone')
		message=request.form.get('message')
		print(name,email,phone,message)
		
		entry=Contacts(name=name,email=email,phone=phone,message=message,dateT=datetime.now())

		# print(entry)

		db.session.add(entry)
		db.session.commit()

		mail.send_message('Message from Blog : '+ name,sender=email,
												   recipients=[params['gmail-user']],
												   body= message+ "\n" +'Phone no. : '+ phone

												   )

	return render_template('contact.html',params=params)

@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):

	post=Posts.query.filter_by(slug=post_slug).first()

	return render_template('post.html',params=params,post=post)

@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):
	if ('user' in session and session['user']==params['admin_user']):
		if request.method=='POST':
			box_title=request.form.get('title')
			tagline=request.form.get('tline')
			slug=request.form.get('slug')
			content=request.form.get('content')
			picture=request.form.get('pics_file')
			dateT=datetime.now()

			if sno=='0':
				post=Posts(title=box_title,tag_line=tagline,slug=slug,content=content,pics_file=picture,dateT=dateT)
				db.session.add(post)
				db.session.commit()

			else:
				post=Posts.query.filter_by(sno=sno).first()
				post.title=box_title
				post.slug=slug
				post.tag_line=tagline
				post.content=content
				post.pics_file=picture
				post.dateT=dateT
				db.session.commit()

				return redirect('/edit/'+sno)
	post=Posts.query.filter_by(sno=sno).first()
	return render_template('edit.html',params=params,post=post)

app.run(debug=True)



