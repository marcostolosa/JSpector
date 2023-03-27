# JSpector

JSpector is a Burp Suite extension that passively crawls JavaScript files and automatically creates issues with URLs and endpoints found on the JS files.

## Prerequisites

Before installing JSpector, you need to have Jython installed on Burp Suite.

## Installation

1.  Download the latest version of JSpector
2.  Open Burp Suite and navigate to the `Extensions` tab.
3.  Click the `Add` button in the `Installed` tab.
4.  In the `Extension Details` dialog box, select `Python` as the `Extension Type`.
5.  Click the `Select file` button and navigate to the `JSpector.py`.
6.  Click the `Next` button.
7.  Once the output show "JSpector extension loaded successfully", click the `Close` button.

## Use

- You just have to navigate on your different targets and JSpector will start working in the background by a simple passive crawl.
- A contextual menu is also available if you want to force JSpector to crawl on some targets.

![image](https://user-images.githubusercontent.com/16657045/227887645-d63649cc-1ad9-4cc6-9deb-021645595721.png)
