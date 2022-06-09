from code import interact
from crypt import methods
from distutils.command.config import config
from email.policy import default
from ensurepip import bootstrap
from flask import Flask, render_template, url_for, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import helper.interact as web3Interact
import json
import logging
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
#mysql+mysqlconnector://<user>:<password>@<host>[:<port>]/<dbname>
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:saxovts@localhost:3306/emperor'
db = SQLAlchemy(app)

class Todo(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  content = db.Column(db.String(200), nullable=False)
  date_created = db.Column(db.DateTime, default=datetime.utcnow)

  def __repr__(self) -> str:
    return '<Task %r>' % self.id

class Payment(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(100), nullable=False)
  contract_address = db.Column(db.String(100), nullable=True)
  payment_address1 = db.Column(db.String(100), nullable=False)
  payment_address2 = db.Column(db.String(100), nullable=True)
  share1 = db.Column(db.Integer, nullable=False)
  share2 = db.Column(db.Integer, nullable=True)
  date_created = db.Column(db.DateTime, default=datetime.utcnow)

  def __repr__(self) -> str:
    return '<Payment %r>' % self.id

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

@app.route('/listings', methods=['GET','POST'])
def listings():
  if request.method == 'GET':
    listings = web3Interact.getListings()
    app.logger.info(listings)
    return render_template('listings.html', listings=listings)
  else:
    tokenId = request.form['tokenId']
    price = request.form['price']
    paymentSplitterAddress = request.form['paymentSplitterAddress']
    try:
      receipt = web3Interact.createListing(tokenId, price, paymentSplitterAddress)
      if receipt is not None:
        #return jsonify({"status": "ok","data": receipt})
        listings = web3Interact.getListings()
        app.logger.info(listings)
        return render_template('listings.html', listings=listings)
      else:
        return jsonify({
          "status": "failed",
          "data": None
        })
    except Exception as e:
      return jsonify({
          "status": "failed",
          "data": None,
          "message": str(e)
        })

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
  
@app.route('/payment', methods=['GET','POST'])
def payment():
  if request.method == 'POST':
    title = request.form['title']
    address1 = request.form['address1']
    address2 = request.form['address2']
    share1 = request.form['share1']
    share2 = request.form['share2']

    addressArr = []
    addressArr.append(address1)
    if address2 !='':
      addressArr.append(address2)
    
    shareArr = []
    shareArr.append(int(share1))
    if share2 !='':
      shareArr.append(int(share2))
    else:
      share2 = 0

    contractAddress = web3Interact.createPayment(title,addressArr, shareArr)

    new_payment = Payment(title=title, contract_address=contractAddress, payment_address1=address1, \
      payment_address2=address2, share1=share1, share2=share2)

    try:
      db.session.add(new_payment)
      db.session.commit()
      return redirect('/payment')
    except Exception as e:
      app.logger.info(e)
      return 'There was in issue adding your payment'
  else:
    payments = Payment.query.order_by(Payment.date_created).all() 
    wrappedPayments = []
    for payment in payments:
      balanceTemp = web3Interact.getBalanceOfAddress(payment.contract_address)
      wrappedPayment = {}
      wrappedPayment['payment'] = payment
      wrappedPayment['balance'] = balanceTemp
      wrappedPayments.append(wrappedPayment)

    return render_template('payment.html', wrappedPayments = wrappedPayments)
  

@app.route('/payment/release', methods=['GET'])
def releasePayment():
    paymentContractAddress = request.args.get('contractAddress')
    releaseAddress = request.args.get('releaseAddress')
    receipt = web3Interact.releasePayment(paymentContractAddress,releaseAddress)
    if receipt is not None:
      return jsonify({"status": "ok","data": receipt})
    else:
      return jsonify({
        "status": "failed",
        "data": None
      })

@app.route('/collection', methods=['GET'])
def displayAdminOwnedNFTs():
  nfts = web3Interact.getAdminOwnedNFTs()
  
  return render_template('collection.html', nfts = nfts)

@app.route('/nft/<int:tokenId>', methods=['GET'])
def displayNFT(tokenId):
  nft = web3Interact.getNFTByTokenId(tokenId)
  payments = Payment.query.order_by(Payment.date_created).all()
  return render_template('nft.html', nft=nft, payments = payments)


if __name__== "__main__":
  app.run(debug=True)