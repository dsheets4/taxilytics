"""
Created on Sep 19, 2014

@author: dingbat
"""

import time

from PyQt4.QtCore import QUrl, QSize
from PyQt4.QtGui import QApplication, QImage, QPainter
from PyQt4.QtWebKit import QWebView

import util

from . import logger


class Screenshot(QWebView):
    """
    Class to grab a screenshot of a web page. 
    Adapted from: http://webscraping.com/blog/Webpage-screenshots-with-webkit/
    """
    def __init__(self):
        self.app = QApplication([__file__])
        
        super(Screenshot, self).__init__()
        self._loaded = False
        self.loadFinished.connect(self._load_finished)
        
    def __del__(self):
        self.app.exit()

    def capture(
            self,
            url,
            output_file,
            page_size=(1024,720),
            img_size=None,
            post_load_delay=0):
        
        self.output_file = output_file
        self.img_size = img_size
        self.post_load_delay = post_load_delay
        
        if not img_size:
            img_size = page_size
        self.img_size = QSize()
        self.img_size.setWidth(img_size[0])
        self.img_size.setHeight(img_size[1])

        size = QSize()
        size.setWidth(page_size[0])
        size.setHeight(page_size[1]) 
        self.page().setViewportSize(size)
        
        self.load(QUrl(url))
            
        while not self._loaded:
            self.app.processEvents()
            time.sleep(0)
        self._loaded = False

    def _load_finished(self, result):
        if self.post_load_delay > 0:
            logger.debug("Waiting {} seconds for page to run after load".format(self.post_load_delay))
            time.sleep(int(self.post_load_delay))
            
        frame = self.page().mainFrame()
        image = QImage(self.img_size, QImage.Format_ARGB32)
        painter = QPainter(image)
        frame.render(painter)
        painter.end()
        image.save(self.output_file)
        
        self._loaded = True
        

def dict_to_ul(settings):
    sList = '<ul>'
    for s in sorted(settings):
        sList = '{}{}'.format(
            sList,''.join([
                '<li>',
                '<b>{}</b>: {}'.format(s,settings[s]),
                '</li>\n'
            ])
        )
    return '{}</ul>'.format(sList)


if __name__ == '__main__':
    from argparse import ArgumentParser
    import ast
    
    parser = ArgumentParser(description="Capture a screenshot")
    parser.add_argument(
                "url",
                metavar="URL",
                help="URL of the page to capture.")
    parser.add_argument(
                "png",
                metavar="PNG",
                help="Name of a PNG output file.")
    parser.add_argument(
                "-a", "--arguments",
                dest="other",
                metavar="{dict}",
                help="Python dictionary of arguments for Screenshot.")

    util.default_args(parser)    
    args = parser.parse_args()
    util.setup_logging(args)
    
    Screenshot().capture(
        args.url,
        args.png,
        **ast.literal_eval(args.other)
    )
    