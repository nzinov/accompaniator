import pickle

with open('rf_nottingham.pkl', 'rb') as f:
    m = pickle.load(f)
    
import sklearn2pmml
m_proxy = sklearn2pmml.EstimatorProxy(m)
pipeline = sklearn2pmml.PMMLPipeline([
	("classifier", m_proxy)
])
sklearn2pmml.sklearn2pmml(pipeline, "model.pmml")
