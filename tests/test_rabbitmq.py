__author__ = 'zeno'
import pika

def sending():
    connection = pika.BlockingConnection(pika.ConnectionParameters(
                   'localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='qname')
    channel.basic_publish(exchange='',
                      routing_key='qname',
                      body='Hello World!')
    print " [x] Sent 'Hello World!'"
    connection.close()

def receiving():
    connection = pika.BlockingConnection(pika.ConnectionParameters(
                   'localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='qname')
    channel.basic_consume(callback,
                      queue='qname',
                      no_ack=True)
    #channel.start_consuming()

def callback(ch, method, properties, body):
    print " [x] Received %r" % (body,)


if __name__=='__main__':
    sending()
    receiving()