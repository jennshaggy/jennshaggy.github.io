import java.io.FileInputStream;
import java.io.ObjectInputStream;
import java.nio.file.Files;
import java.nio.file.Path;

public class VerifyOath {
    public static void main(String[] args) throws Exception {
        Path proof = Path.of("/tmp/oathforger-proof");
        Files.deleteIfExists(proof);

        try (ObjectInputStream in =
                 new ObjectInputStream(new FileInputStream(args[0]))) {
            in.readObject();
        } catch (Throwable error) {
            System.out.println(
                "post_execution_exception=" + error.getClass().getSimpleName()
            );
        }

        System.out.println("sink_executed=" + Files.exists(proof));
    }
}
