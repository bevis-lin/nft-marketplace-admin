from code import interact
from distutils.command.config import config
from email.policy import default
from flask import Flask, render_template, url_for, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import helper.interact as web3Interact
import json
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class Todo(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  content = db.Column(db.String(200), nullable=False)
  date_created = db.Column(db.DateTime, default=datetime.utcnow)

  def __repr__(self) -> str:
    return '<Task %r>' % self.id


@app.route('/', methods=['GET','POST'])
def index():
  if request.method == 'POST':
    task_content = request.form['content']
    new_task = Todo(content=task_content)

    try:
      db.session.add(new_task)
      db.session.commit()
      return redirect('/')
    except:
      return 'There was in issue adding your task'
  else:
    tasks = Todo.query.order_by(Todo.date_created).all()
    return render_template('index.html', tasks = tasks)

@app.route('/delete/<int:id>')
def delete(id):
  task_to_delete = Todo.query.get_or_404(id)
  try:
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect('/')
  except:
    return 'There was a problem deleting that task'

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
  task = Todo.query.get_or_404(id)

  if request.method == 'POST':
    task.content = request.form['content']
    try:
      db.session.commit()
      return redirect('/')
    except:
      return 'There was a problem updating that task'
  else:
    return render_template('update.html', task=task)

@app.route('/listings', methods=['GET'])
def listings():
  listings = web3Interact.getListings()
  app.logger.info(listings)
  return render_template('listings.html', listings=listings)

@app.route('/listings/<int:listingId>/purchase', methods=['GET'])
def purchase(listingId):
  #check if listingId valid
  listings = web3Interact.getListings()
  if not any(d['listingId'] == listingId for d in listings):
    return 'listing id not exists', 404
  try:

  
    txHash = web3Interact.purchaseListing(listingId)

    if txHash is not None:

      return jsonify({
        "status": "ok",
        "data": txHash
      })
    else:
      raise Exception('get null txHash')
  except Exception as e:
    return jsonify({
          "status": "failed",
          "data": None,
          "message": str(e)
        })


@app.route('/transaction/<string:txHash>/receipt', methods=['GET'])
def getTransactionReceipt(txHash):
  receipt = web3Interact.getTransactionReceipt(txHash)
  if receipt is not None:
    return jsonify({"status": "ok","data": receipt})
  else:
    return jsonify({
      "status": "failed",
      "data": None
    }) 

if __name__== "__main__":
  app.run(debug=True)