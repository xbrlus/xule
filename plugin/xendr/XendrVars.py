class XendrVars:
    
    @classmethod
    def set(cls, cntlr, name, value):
        if not hasattr(cntlr, 'xendr_vars'):
            cntlr.xendr_vars = dict()
        
        cntlr.xendr_vars[name] = value
        return cntlr.xendr_vars[name]
    
    @classmethod
    def get(cls, cntlr, name):
        if hasattr(cntlr, 'xendr_vars'):
            return cntlr.xendr_vars.get(name)
        else:
            return None

def save_arelle_model(model):
    # The arelle model is saved as a dictionary keyed by id() of the model
    cntlr = model.modelManager.cntlr
    arelle_models = XendrVars.get(cntlr, 'arelle-models') or XendrVars.set(cntlr, 'arelle-models', dict())
    if id(model) not in arelle_models:
        arelle_models[id(model)] = model

def get_arelle_model(cntlr, model_id):
    arelle_models = XendrVars.get(cntlr, 'arelle-models') or XendrVars.set(cntlr, 'arelle-models', dict())
    return arelle_models.get(model_id)

def get_arelle_models(cntlr):
    arelle_models = XendrVars.get(cntlr, 'arelle-models') or XendrVars.set(cntlr, 'arelle-models', dict())
    return arelle_models.values()