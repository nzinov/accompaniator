import org.dmg.pmml.PMML;
import org.jpmml.model.SerializationUtil;

import javax.xml.bind.JAXBException;

import org.jpmml.model.visitors.LocatorNullifier;
import org.nustaq.serialization.FSTConfiguration;
import org.nustaq.serialization.FSTObjectOutput;
import org.xml.sax.SAXException;

import java.io.*;

public class Converter {
    public static PMML load(InputStream is) throws JAXBException, SAXException {
        return org.jpmml.model.PMMLUtil.unmarshal(is);
    }

    static FSTConfiguration conf = FSTConfiguration.createDefaultConfiguration();

    public static void myWriteMethod( OutputStream stream, Object toWrite ) throws IOException
    {
        FSTObjectOutput out = new FSTObjectOutput(stream, conf);
        out.writeObject( toWrite );
        out.close(); // required !
    }

    public static void main(String[] args) {
        try (OutputStream os = new FileOutputStream("model_fst.ser"); InputStream is = new FileInputStream("model.pmml")) {
            PMML pmml = load(is);
            LocatorNullifier locatorNullifier = new LocatorNullifier();
            locatorNullifier.applyTo(pmml);

            /*byte barray[] = conf.asByteArray(pmml);
            os.write(barray);*/
            myWriteMethod(os, pmml);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
