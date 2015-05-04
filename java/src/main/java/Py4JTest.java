import py4j.GatewayServer;

public class Py4JTest {

    public int addition(int first, int second) {
        return first + second;
    }

    public static void main(String[] args) {
        Py4JTest test = new Py4JTest();
        GatewayServer server = new GatewayServer(test);
        server.start();
    }
}
