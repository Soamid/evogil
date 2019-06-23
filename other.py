import time

from thespian.actors import ActorSystem

from util.temp import Bubak

if __name__ == '__main__':
    bubak = ActorSystem("multiprocTCPBase").createActor(Bubak)
    ActorSystem().ask(bubak, "create")
    t = time.time()
    # print(ActorSystem().tell(bubak, "epoch"))
    end = ActorSystem().listen()
    print(time.time() - t)
    ActorSystem().shutdown()
