import subprocess



def bash(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

def version(name):
    return bash([name, '--version']).split(' ')
    