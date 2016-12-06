import sys, json, time, requests

def print_results(results):
    def list_print(lst, phrase):
        print phrase + "=" * 80
        for item in lst:
            print "::".join(item[:3])
    list_print([x for x in results if x[3]], "SUCCESSES")
    list_print([x for x in results if not x[3]], "FAILURES")


def log_message(str, dbg=True):
    if dbg:
        print str
        sys.stdout.flush()


def invoke_api(payload, url, auth, retries, begin="start/", status_success=False):
    # send task to api
    log_message(url + begin + "| data: " + str(payload))
    r = requests.post(url + begin, data=payload, auth=auth)
    #log_message(r.request.body)

    if status_success:
        return r.status_code == 200

    if r.status_code != 200:
        raise Exception("Error while talking to the mbed API")

    response = r.json()
    log_message(response)
    uuid = response['result']['data']['task_id']
    log_message("Task accepted and given ID: %s" % uuid)
    success = False
    messages = [response]

    # poll for output
    for check in range(0, retries):
        log_message("Checking for output: cycle %s of %s" % (check, retries))
        time.sleep(1)
        r = requests.get(url + "output/%s" % uuid, auth=auth)
        messages.append(r.content)
        response = r.json()
        if response['result']['data']['task_complete']:
            log_message("Task completed.")
            success = bool(response['result']['data']['compilation_success'])
            break

    if not success:
        print "FAILURE" + "=" * 80
        for m in messages:
            log_message(m)

    return success


def build_repo(target, program='test-rev80', user='ServiceMonitor', pw='coverage100', retries=25, url="https://developer.mbed.org/api/v2/tasks/compiler/"):
    payload = {'clean':True, 'target':target, 'program':program}
    auth = (user, pw)
    return invoke_api(payload, url, auth, retries)

def export_repo(target, program='test-rev80', user='ServiceMonitor', pw='coverage100', retries=25, url="https://developer.mbed.org/api/v2/export/"):
    payload = {'target':target, 'project':program, 'type':'uvision5'}
    auth = (user, pw)
    return invoke_api(payload, url, auth, retries, begin='', status_success=True)


if __name__ == '__main__':
    tests = ["test-rev90", "test-rev120", "test-rev130", "test-dev", "test-os-5-2"]
    targets = ["K64F"]
    total = len(targets)*len(tests)
    results = []
    count, passes = 0, 0
    for target in targets:
        for test in tests:
            count += 1
            print "%s/%s"%(count, total)
            sys.stdout.flush()
            result_exp = export_repo(target, test)
            result = build_repo(target,test)
            results.append((target, test, "compile",result))
            results.append((target, test, "export", result))
            passes += (int)(result)
    print("%s/%s passing" % (passes, total))
    print_results(results)

