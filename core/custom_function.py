from statsmodels.tsa.ar_model import AutoRegResults

def example_arrivals_time(case):
    loaded = AutoRegResults.load('example/example_arrivals/arrival_AutoReg_model.pkl')
    return loaded.predict(case+1, case+1)[0]