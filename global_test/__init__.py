from selenium import webdriver

def create_browser():
	#binary = webdriver.firefox.firefox_binary.FirefoxBinary('/opt/firefox/firefox')
	#browser = webdriver.Firefox(firefox_binary=binary)
	browser = webdriver.Firefox()
	
	browser.implicitly_wait(5)
	browser.maximize_window()
	
	return browser
