from validation.validate import validate
import json
print(json.dumps(validate("../data/generated"), indent=2))
