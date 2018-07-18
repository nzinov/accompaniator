import org.dmg.pmml.PMML;
import org.jpmml.model.SerializationUtil;

import javax.xml.bind.JAXBException;

import org.jpmml.model.visitors.LocatorNullifier;
import org.xml.sax.SAXException;

import java.io.*;

public class Converter {
    public static PMML load(InputStream is) throws JAXBException, SAXException {
        return org.jpmml.model.PMMLUtil.unmarshal(is);
    }

    public static void main(String[] args) {
        try (OutputStream os = new FileOutputStream("model.ser"); InputStream is = new FileInputStream("model.pmml")) {
            PMML pmml = load(is);
            LocatorNullifier locatorNullifier = new LocatorNullifier();
            locatorNullifier.applyTo(pmml);
            ObjectOutputStream oos = new ObjectOutputStream(os);
            oos.writeObject(pmml);
            oos.close();
            //SerializationUtil.serializePMML(pmml, os);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
