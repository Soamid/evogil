from thespian.actors import Actor


def prime_number(num):
    # If given number is greater than 1
    if num > 1:

        # Iterate from 2 to n / 2
        for i in range(2, num):

            # If num is divisible by any number between
            # 2 and n / 2, it is not prime
            if (num % i) == 0:
                print(num, "is not a prime number")
                return False
        else:
            print(num, "is a prime number")
            return True

    else:
        print(num, "is not a prime number")
        return False

class Node(Actor):
    def receiveMessage(self, message, sender):
        self.send(sender, message[0](message[1]))






class Bubak(Actor):

    def create_nodes(self):
        print("CREATING NODES")
        self.primes = [179424691]
        self.nodes = [self.createActor(Node) for _ in range(len(self.primes))]
        self.start_epoch()

    def start_epoch(self):
        print("EPOCH START")
        for i in range(len(self.nodes)):
            self.counter = 0
            self.send(self.nodes[i], (prime_number, self.primes[i]))

    def receiveMessage(self, msg, sender):
        print("MESSAGE RECEIVED : " + str(msg))
        if msg == "create":
            self.parent = sender
            self.create_nodes()
            self.send(sender, 'done')
        elif msg == "epoch":
            self.start_epoch()
        else:
            print("new population: " + str(msg))
            self.counter += 1

            if self.counter == len(self.nodes):
                self.send(self.parent, 'endgame')

