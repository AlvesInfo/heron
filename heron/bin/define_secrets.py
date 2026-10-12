import io
import os
import random
import string
import json


def generate_secret_key(size=50):
    pool = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.SystemRandom().choice(pool+str(i)) for i in range(size))


def secret_key_from_json_file(file_path, file_perms, env_var, create=True, size=50):
    try:
        with io.open(file_path, 'r') as f:
            try:
                secrets = json.load(f)
                if env_var in secrets:
                    return secrets[env_var]

                with io.open(file_path, 'w') as fw:
                    key = generate_secret_key(size)
                    secrets[env_var] = key
                    fw.write(json.dumps(secrets, indent=2))
                    return key
                
            except json.decoder.JSONDecodeError:
                with io.open(file_path, 'w') as fw:
                    key = generate_secret_key(size)
                    dic = {"FILENAME": "secrets.json", env_var: key}
                    fw.write(json.dumps(dic, indent=2))
                    return key

    except IOError as e:
        if e.errno == 2 and create:
            with io.open(file_path, 'w') as f:
                key = generate_secret_key(size)
                dic = {"FILENAME": "secrets.json", env_var: key}
                f.write(json.dumps(dic, indent=2))
            if file_perms:
                os.chmod(file_path, int(str(file_perms), 8))
            return key
        raise


def get_secret_key(
        file_path="heron/ignore/secrets.json",
        create=True,
        size=50,
        file_perms=None,
        env_var="DJANGO_SECRET_KEY"
):
    try:
        return os.environ[env_var]
    except KeyError:
        if file_path:
            return secret_key_from_json_file(file_path, file_perms, env_var, create=create, size=size)
        raise


if __name__ == '__main__':
    print(generate_secret_key())
