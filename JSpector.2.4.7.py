from burp import (IBurpExtender, IHttpListener, IScannerListener,
                  IExtensionStateListener, IContextMenuFactory, IScanIssue)
import re
from java.util import ArrayList
from javax.swing import JMenuItem, JOptionPane
from java.awt import Toolkit
from java.awt.datatransfer import StringSelection

class BurpExtender(IBurpExtender, IHttpListener, IScannerListener, IExtensionStateListener, IContextMenuFactory):

    def __init__(self):
        self._exclusion_regex = re.compile(r'http://www\.w3\.org')
        self._url_pattern = re.compile(r'(?:http|https|ftp|ftps|sftp|file|tftp|telnet|gopher|ldap|ssh)://[^\s"<>]+')
        self._endpoint_pattern1 = re.compile(r'(?:(?<=["\'])/(?:[^/"\']+/?)+(?=["\']))')
        self._endpoint_pattern2 = re.compile(r'http\.(?:post|get|put|delete|patch)\(["\']((?:[^/"\']+/?)+)["\']')
        self._invocation = None
        self._scanned_js_files = set()

    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()

        callbacks.setExtensionName("JSpector")
        callbacks.registerHttpListener(self)
        callbacks.registerScannerListener(self)
        callbacks.registerExtensionStateListener(self)
        callbacks.registerContextMenuFactory(self)

        print("JSpector extension loaded successfully.\nWarning: the size of the output console content is limited, we recommend that you save your results in a file.")
        
    def processHttpMessage(self, toolFlag, messageIsRequest, messageInfo):
        if not messageIsRequest and self._callbacks.isInScope(messageInfo.getUrl()):
            js_url = messageInfo.getUrl().toString()
            if toolFlag == self._callbacks.TOOL_PROXY and js_url in self._scanned_js_files:
                return

            if js_url in self._scanned_js_files:
                return
            else:
                self._scanned_js_files.add(js_url)

            response = messageInfo.getResponse()
            if response:
                response_info = self._helpers.analyzeResponse(response)
                headers = response_info.getHeaders()

                content_type = next((header.split(':', 1)[1].strip() for header in headers if header.lower().startswith('content-type:')), None)

                if content_type and 'javascript' in content_type.lower():
                    body = response[response_info.getBodyOffset():]
                    urls = self.extract_urls_from_js(body)
                    if urls:
                        self.create_issue(messageInfo, urls)
                    if toolFlag == self._callbacks.TOOL_PROXY:
                        self._scanned_js_files.add(js_url)
                            
    def extract_urls_from_js(self, js_code):
        urls = set(re.findall(self._url_pattern, js_code))
        endpoints1 = set(re.findall(self._endpoint_pattern1, js_code))
        endpoints2 = set(re.findall(self._endpoint_pattern2, js_code))

        urls = set(url for url in urls if not self._exclusion_regex.search(url))

        return urls.union(endpoints1, endpoints2)

    def create_issue(self, messageInfo, urls):
        issue = JSURLsIssue(self._helpers, messageInfo, urls)
        self._callbacks.addScanIssue(issue)
        js_full_url = messageInfo.getUrl().toString()
        self.output_results(urls, js_full_url)

    def extensionUnloaded(self):
        print("JSpector extension unloaded.")

    def newScanIssue(self, issue):
        pass

    def createMenuItems(self, invocation):
        self._invocation = invocation
        menu_items = ArrayList()

        menu_item1 = JMenuItem("Export URLs to clipboard",
                                actionPerformed=self.export_urls_to_clipboard)
        menu_items.add(menu_item1)

        menu_item2 = JMenuItem("Export endpoints to clipboard",
                                actionPerformed=self.export_endpoints_to_clipboard)
        menu_items.add(menu_item2)

        menu_item3 = JMenuItem("Export all results to clipboard",
                                actionPerformed=self.export_results_to_clipboard)
        menu_items.add(menu_item3)

        return menu_items

    def export_urls_to_clipboard(self, event):
        messages = self._invocation.getSelectedMessages()
        if messages is None:
            JOptionPane.showMessageDialog(None, "No JS file selected.")
            return

        all_results = ""

        for message in messages:
            if self._callbacks.isInScope(message.getUrl()):
                js_url = message.getUrl().toString()
                if js_url in self._scanned_js_files:
                    response = message.getResponse()
                    if response:
                        response_info = self._helpers.analyzeResponse(response)
                        headers = response_info.getHeaders()

                        content_type = next((header.split(':', 1)[1].strip() for header in headers if header.lower().startswith('content-type:')), None)

                        if content_type and 'javascript' in content_type.lower():
                            body = response[response_info.getBodyOffset():]
                            urls = self.extract_urls_from_js(body)
                            if urls:
                                urls_list, _ = self.sort_urls_endpoints(urls)
                                for url in urls_list:
                                    all_results += url + "\n"

        self.copy_results_to_clipboard(all_results)

    def export_endpoints_to_clipboard(self, event):
        messages = self._invocation.getSelectedMessages()
        if messages is None:
            JOptionPane.showMessageDialog(None, "No JS file selected.")
            return

        all_results = ""

        for message in messages:
            if self._callbacks.isInScope(message.getUrl()):
                js_url = message.getUrl().toString()
                if js_url in self._scanned_js_files:
                    response = message.getResponse()
                    if response:
                        response_info = self._helpers.analyzeResponse(response)
                        headers = response_info.getHeaders()

                        content_type = next((header.split(':', 1)[1].strip() for header in headers if header.lower().startswith('content-type:')), None)

                        if content_type and 'javascript' in content_type.lower():
                            body = response[response_info.getBodyOffset():]
                            urls = self.extract_urls_from_js(body)
                            if urls:
                                _, endpoints_list = self.sort_urls_endpoints(urls)
                                for endpoint in endpoints_list:
                                    all_results += endpoint + "\n"

        self.copy_results_to_clipboard(all_results)

    def copy_results_to_clipboard(self, all_results):
        if all_results:
            clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
            clipboard.setContents(StringSelection(all_results), None)
            JOptionPane.showMessageDialog(None, "Results exported to clipboard.")
        else:
            JOptionPane.showMessageDialog(None, "No results found to export.")


    def export_results_to_clipboard(self, event):
        messages = self._invocation.getSelectedMessages()
        if messages is None:
            JOptionPane.showMessageDialog(None, "No JS file selected.")
            return

        all_results = ""

        for message in messages:
            if self._callbacks.isInScope(message.getUrl()):
                js_url = message.getUrl().toString()
                if js_url in self._scanned_js_files:
                    response = message.getResponse()
                    if response:
                        response_info = self._helpers.analyzeResponse(response)
                        headers = response_info.getHeaders()

                        content_type = next((header.split(':', 1)[1].strip() for header in headers if header.lower().startswith('content-type:')), None)

                        if content_type and 'javascript' in content_type.lower():
                            body = response[response_info.getBodyOffset():]
                            urls = self.extract_urls_from_js(body)
                            if urls:
                                results = self.format_results(js_url, urls)
                                all_results += results

        if all_results:
            clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
            clipboard.setContents(StringSelection(all_results), None)
            JOptionPane.showMessageDialog(None, "Results exported to clipboard.")
        else:
            JOptionPane.showMessageDialog(None, "No results found to export.")

    def format_results(self, js_full_url, urls):
        urls_list, endpoints_list = self.sort_urls_endpoints(urls)

        formatted_results = ""

        for url in urls_list:
            formatted_results += url + "\n"

        for endpoint in endpoints_list:
            formatted_results += endpoint + "\n"

        return formatted_results

    def output_results(self, urls, js_full_url):
        urls_list, endpoints_list = self.sort_urls_endpoints(urls)

        print("JSpector results for {}:".format(js_full_url))
        print("-----------------")

        print("URLs found ({}):".format(len(urls_list)))
        print("-----------------")
        for url in urls_list:
            print(url)

        print("\nEndpoints found ({}):".format(len(endpoints_list)))
        if endpoints_list:
            print("-----------------")
            for endpoint in endpoints_list:
                print(endpoint)
        else:
            print("No endpoints found.")

        print("-----------------")

    @staticmethod
    def sort_urls_endpoints(urls):
        urls_list = []
        endpoints_list = []

        for url in urls:
            if re.match('^(?:http|https|ftp|ftps|sftp|file|tftp|telnet|gopher|ldap|ssh)://', url):
                urls_list.append(url)
            else:
                endpoints_list.append(url)

        urls_list.sort()
        endpoints_list.sort()

        return urls_list, endpoints_list

class JSURLsIssue(IScanIssue):

    def __init__(self, helpers, messageInfo, urls):
        self._helpers = helpers
        self._httpService = messageInfo.getHttpService()
        self._url = messageInfo.getUrl()
        self._urls = urls

    def getUrl(self):
        return self._url

    def getHttpMessages(self):
        return []

    def getHttpService(self):
        return self._httpService

    def getIssueName(self):
        return "JSPector results"

    def getIssueType(self):
        return 0x08000000

    def getSeverity(self):
        return "Information"

    def getConfidence(self):
        return "Certain"

    def getIssueBackground(self):
        return "The following URLs were found in a JavaScript file. This information may be useful for further testing."

    def getRemediationBackground(self):
        return None

    def getIssueDetail(self):
        urls_list, endpoints_list = BurpExtender.sort_urls_endpoints(self._urls)

        details = self.build_list("URLs found", urls_list)
        details += self.build_list("Endpoints found", endpoints_list)

        return details

    def getRemediationDetail(self):
        return None

    @staticmethod
    def build_list(title, items):
        if not items:
            return ""

        details = "<b>{title} ({num_items}):</b>".format(title=title, num_items=len(items))
        details += "<ul>"

        for item in items:
            details += "<li>{item}</li>".format(item=item)

        details += "</ul>"

        return details
