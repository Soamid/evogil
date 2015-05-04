
from py4j.java_gateway import JavaGateway

gateway = JavaGateway()
random = gateway.jvm.java.util.Random()
n1 = random.nextInt(10)
n2 = random.nextInt(10)
print(n1, n2)

app = gateway.entry_point
print(app.addition(n1, n2))