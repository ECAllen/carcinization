import anthropic

client = anthropic.Anthropic()


def list_models():
    models = client.models.list()
    for model in models.data:
        print(model.id)


list_models()
