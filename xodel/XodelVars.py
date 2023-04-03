class XodelVars:
    
    @classmethod
    def set(cls, cntlr, name, value):
        if not hasattr(cntlr, 'xodel_vars'):
            cntlr.xodel_vars = dict()
        
        cntlr.xodel_vars[name] = value
        return cntlr.xodel_vars[name]
    
    @classmethod
    def get(cls, cntlr, name):
        if hasattr(cntlr, 'xodel_vars'):
            return cntlr.xodel_vars.get(name)
        else:
            return None

def save_arelle_model(model):
    # The arelle model is saved as a dictionary keyed by id() of the model
    cntlr = model.modelManager.cntlr
    arelle_models = XodelVars.get(cntlr, 'arelle-models') or XodelVars.set(cntlr, 'arelle-models', dict())
    if id(model) not in arelle_models:
        arelle_models[id(model)] = model

def get_arelle_model(cntlr, model_id):
    arelle_models = XodelVars.get(cntlr, 'arelle-models') or XodelVars.set(cntlr, 'arelle-models', dict())
    return arelle_models.get(model_id)