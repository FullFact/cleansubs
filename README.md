# Overview

This repo aims to take subtitle streams in various formats from an MQTT feed, and transform the raw text into sentences.


### Edge cases

Most of the time a sentence ends when there is a full stop. There are many situations where this is not the case.

1. ? question marks
2. ! exclamation marks
3. . . . three full stops as elipses
4. "Quotation marks"
5. Sentences with more than one end marker in them
6. Mr. Corbyn, Mrs. May etc. (Full stop followed by capital letter looks very much like the end of a sentence)
7. 2.1 decimal points
8. .org, .com, .co.uk, URLs and email addresses

More will be discovered by creating test cases from the raw subtitles.

### Types of subtitles

Additive subtitles ('The', 'The cat', 'The cat sat'…), etc.

TODO: figure out what different types we'll be dealing with, we may not know all the types until we create enough test cases.

## Creating test cases

Create new test cases by retrieving samples of subtitles from the an MQTT subtitles feed. These can be retrieved using mosquitto, which can be downloaded like this `sudo apt-get install mosquitto mosquitto-client` and used to get subtitles like this: `mosquitto_sub -h your_host_here -t "path/to/the/topic"`.

A test case goes inside its own, descriptively named, directory inside `tests`. It should have a file called `before.sub` with the raw subtitles in it, and a file called `after.sub` with those subtitles manually edited into the sentences you'd expect to get from them once they've been processed.

## Running tests

Running `python -m unittest test_cleansubs.py` iterates through all the test cases in `tests`, processes `before.subs` and checks to see if the result matches `after.subs`.

## Processing a stream in real time

The stream to use is this one: `mosquitto_sub -h your_host_here -t "path/to/the/topic"`.

It can be piped into `sentence_stream.py` like so:
`mosquitto_sub -h your_host_here -t "path/to/the/topic" | python3 sentence_stream.py`.

This will print out each sentence in the subtitles line by line.
