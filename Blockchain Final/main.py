########################################################################################
######################          Import packages      ###################################
########################################################################################
from flask import Blueprint, render_template, flash, Flask, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from __init__ import create_app, db
import hashlib
import json
from time import time
from uuid import uuid4
from urllib.parse import urlparse
from models import User
import smtplib 
from datetime import datetime
from pathlib import Path
import re

path = Path(__file__).parent.absolute()
########################################################################################
# our main blueprint
main = Blueprint('main', __name__)

app = create_app() # we initialize our flask app using the __init__.py function
@main.route('/') # home page that return 'index'
def index():
    return render_template('index.html')

@main.route('/profile') # profile page that return 'profile'
@login_required
def profile():
    return render_template('profile.html', data= str(current_user.id) + ","+ current_user.name + "," + current_user.email + "," + current_user.phonenumber + "," + current_user.dateofbirth + "," + current_user.IBAN + "," + str(current_user.amount))

@main.route('/transactions') # profile page that return 'profile'
@login_required
def transactions():
    file1 = open(str(path) + "\\transactions.txt", 'r')
    lines = []
    while True:
        
        line = file1.readline()

        if not line:
            break
        
        if line.strip() == str(current_user.id):
            item = {"dateTime": file1.readline(), "description": file1.readline(), "amount": file1.readline(), "balance": file1.readline()}
            lines.append(item)
        
  
    file1.close()
    return render_template('transactions.html', data= lines)


@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/contact')
def contact():
    return render_template('contact_us.html')

@main.route('/privacy')
def privacy():
    return render_template('privacy_policy.html')

@main.route('/transfer') # transfer page that return 'transfer'
@login_required
def transfer():
    return render_template('transfer.html')

@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)


class BlockChain(object):
    """ Main BlockChain class """
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        # create the genesis block
        self.new_block(previous_hash=1, proof=100)

    @staticmethod
    def hash(block):
        # hashes a block
        # also make sure that the transactions are ordered otherwise we will have insonsistent hashes!
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def new_block(self, proof, previous_hash=None):
        # creates a new block in the blockchain
        block = {
            'index': len(self.chain)+1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    @property
    def last_block(self):
        # returns last block in the chain
        return self.chain[-1]

    def new_transaction(self, sender, recipient, amount):
        # adds a new transaction into the list of transactions
        # these transactions go into the next mined block
        self.current_transactions.append({
            "sender":sender,
            "recient":recipient,
            "data":amount,
        })
        return int(self.last_block['index'])+1

    def proof_of_work(self, last_proof):
        # simple proof of work algorithm
        # find a number p' such as hash(pp') containing leading 4 zeros where p is the previous p'
        # p is the previous proof and p' is the new proof
        proof = 0
        while self.validate_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def validate_proof(last_proof, proof):
        # validates the proof: does hash(last_proof, proof) contain 4 leading zeroes?
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self, address):
        # add a new node to the list of nodes
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def full_chain(self):
        # xxx returns the full chain and a number of blocks
        pass


# generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
# initiate the Blockchain
blockchain = BlockChain()

@app.route('/mine', methods=['POST'])
def mine():
    user1 = User.query.filter_by(id=current_user.id).first()

    if user1.amount < int(request.form.get('amount')):
        flash('Your balance is insuffient to cover this transaction')
    else:
        # first we need to run the proof of work algorithm to calculate the new proof..
        last_block = blockchain.last_block
        last_proof = last_block['proof']
        proof = blockchain.proof_of_work(last_proof)

        # we must recieve reward for finding the proof in form of receiving 1 Coin
        blockchain.new_transaction(
            sender= current_user.id,
            recipient= request.form.get('receiver'),
            amount= request.form.get('amount'),
        )

        # forge the new block by adding it to the chain
        previous_hash = blockchain.hash(last_block)
        block = blockchain.new_block(proof, previous_hash)

        response = {
            'message': "Forged new block.",
            'index': block['index'],
            'transactions': block['transactions'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
        }
        user2 = User.query.filter_by(id=int(request.form.get('receiver'))).first()
        user2.amount = user2.amount + int(request.form.get('amount'))
        db.session.commit()
        user1.amount = user1.amount - int(request.form.get('amount'))
        db.session.commit()


        try: 
            smtp = smtplib.SMTP('smtp.gmail.com', 587) 

            smtp.starttls() 

            smtp.login("blockchain.payment.project@gmail.com","Bp123456")
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

            TEXT1 = "This is an email to confirm that you have transfered " + str(request.form.get('amount')) +" SAR\nSender: " + user1.name + "\nReceiver: " + user2.name + "\nDate and Time: " + dt_string
            message1 = 'Subject: {}\n\n{}'.format("Funds Transfered", TEXT1)

            TEXT2 = "This is an email to confirm that you have received " + str(request.form.get('amount')) +" SAR\nSender: " + user1.name + "\nReceiver: " + user2.name + "\nDate and Time: " + dt_string
            message2 = 'Subject: {}\n\n{}'.format("Funds Received", TEXT2)

            smtp.sendmail("blockchain.payment.project@gmail.com",user1.email,message1) 
            smtp.sendmail("blockchain.payment.project@gmail.com",user2.email,message2) 
            file1 = open(str(path) + "\\transactions.txt", "a")
            file1.write(str(user1.id) + "\n" + dt_string + "\nMoney Sent to " + str(user2.name) + "\n" + "-"+str(request.form.get('amount')) + "\n" + str(user1.amount) + "\n") 
            file1.write(str(user2.id) + "\n" + dt_string + "\nMoney Received from " + str(user1.name) + "\n" + "+"+str(request.form.get('amount'))+ "\n" + str(user2.amount) + "\n") 
            file1.close()
            smtp.quit() 
            flash("Transfer was done successfully") 

        except Exception as ex: 
            flash(str(ex))


    return redirect(url_for('main.transfer'))


def new_transaction():

    values = request.get_json()
    required = ['sender', 'recipient', 'amount']

    if not all(k in values for k in required):
        return 'Missing values.', 400

    # create a new transaction
    index = blockchain.new_transaction(
        sender = values['sender'],
        recipient = values['recipient'],
        amount = values['amount']
    )

    response = {
        'message': f'Transaction will be added to the Block {index}',
    }
    return jsonify(response, 200)

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    print('values',values)
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    # register each newly added node
    for node in nodes: blockchain.register_node(node)

    response = {
        'message': "New nodes have been added",
        'all_nodes': list(blockchain.nodes),
    }

    return jsonify(response), 201




if __name__ == '__main__':
    db.create_all(app=create_app()) # create the SQLite database
    app.run(debug=True) # run the flask app on debug mode