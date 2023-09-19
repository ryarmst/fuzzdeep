# FuzzDeep

FuzzDeep is a Python tool for fuzzing Android application deep link handling to identify bugs and security issues. FuzzDeep currently supports:
* Mutation-based fuzzing using Radamsa
* Wordlist-based fuzzing using user-supplied wordlist

### Background

This tool was created to ease the challenge in automating attacks against link handling logic in Android applications. It is not a replacement for static review/analysis but may help identify issues where analysis is complicated by obfuscation or other challenges. The tool was partially inspired by [deeplink-fuzz.sh](https://github.com/B3nac/deeplink-fuzz.sh) which uses Radamsa to fuzz link handlers, but the tool did not have the required flexibility. The tool was also inspired by similar HTTP fuzzing tools as can be seen in its payload positioning implementation.

## Setup

The recommended setup approach to download the repo and instantiate a Python virtual environment. Note that Python 3 (required) is aliased `python3` in some environments. 

Install Virtual Environments if needed
```
python -m pip install --user virtualenv
```

Clone the repo 

Navigate into the repo

Create Project Directory and navigate to it
```
python -m venv env
```

Activate virtual environment - modifying current shell's PATH to new python/pip
```
source env/bin/activate
```

Install the requirements
```
python -m pip install requirements.txt
```

### Requirements
* Python 3
* Pyradamsa
* adb_shell

## Usage

The tool is easy to use, but effective usage is non-trivial. The difficulty is in identifying application behavior that indicates a bug or potential vulnerability. Consider the fuzzing of HTTP services for comparison. When fuzzing web services, the HTTP response from the server can be used for comparison to a baseline to identify whether each payload caused a difference in application behavior. With Android deep links, we don't necessarily expect an output. So what should be monitored to identify an event worth investigating? 

I will recommend you consider some of the following possibilities:
* Using `am monitor` within a separate `adb shell` to monitor for crashes/ANRs.
* Using `logcat` within a separate `adb shell` to monitor log output.
** You may also want to consider modifying the logging behavior (via an app rebuild or dynamic hooking with Frida) to facilitate this process.
* Watching the opening of each launched activity as the attack progresses.
** This may be most useful if you are looking for a specific outcome that has a clear visual marker (such as the popping of an `alert()` box from an XSS attack)
* Using Frida to hook relevant logic to look for abnormalities.
** This is likely the most effective generally technique, but will require some through and will be app-specific. 

Note that for other monitoring tools, you will want to record timestamps to correlate events with each payload submitted.

### Timing and the Activity Lifecycle

When fuzzing a set of payloads, we want to ensure that all of our payloads are actually processed by the application as intended. A naive implementation would simply send payloads as quickly as possible, but this is not likely an effective approach with Android activities. 

The first issue we encounter is where the deep link handling logic is implemented within an activity. If the logic is entirely contained within a method like `onCreate` then deep links will only be handled on creation of the activity. Think about the traditional use case of deep links: the intention is to transition a user from some location outside of the app to a specific activity within an app. If the target activity is already open, triggering additional deep links may not have any impact on the application.

As a result, this tool was built to exit the app following each payload. An important consideration in this cycle is the timing: how long should the application be given to handle each payload? I think this is going to be heavily app- and device-specific. As a result, this was built as a command-line opion (`-s` for sleep). The default is 3 seconds. I would recommend observing the behavior when sending a single payload and determining how long the app takes to "fully open" and finish processing the data. If you are trying to trigger XSS via a deep link that relies on a web service/API response, this will also require waiting the full time for these communications. 

### Example Commands

Fuzz a target package's deep link handler for `scheme://host` using a wordlist to inject payload in the query string parameter `q`
```
python fuzzdeep.py -w "wordlist.txt" -t "scheme://host?q=FUZZ" -p "package.name"
```

Fuzz a target package's deep link handler for `scheme://host` using Radamsa to inject payload in the query string parameter `q` using `value` for mutation
```
python fuzzdeep.py -f "value" -t "scheme://host?q=FUZZ" -p "package.name"
```

### Issues
* If you encounter the error with *LIBUSB_ERROR_BUSY* then you will need ro run `adb kill-server`

## Future Work
The following are on the TODO list:
* Broaden support for Intents beyond deep links.
* Implement better tooling to support identifying interesting outcomes/conditions.
* Add timestamp


