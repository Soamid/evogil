package pl.edu.agh.evogil;


import pl.edu.agh.evogil.algorithm.AlgorithmFactory;
import py4j.GatewayServer;

public class EvogilProvider {

    public AlgorithmFactory getAlgorithmFactory() {
        return new AlgorithmFactory();
    }

    public static void main(String[] args) {
        EvogilProvider provider = new EvogilProvider();

        GatewayServer server = new GatewayServer(provider);
        server.start();
    }
}
