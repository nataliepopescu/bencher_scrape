import scrapy
from scrapy import Request
import json
import re
import subprocess

categ_attributes = {
    'bencher_rev_deps': {
        'url': 'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page={page}&per_page={per_page}',
        'per_page': 10,
        'total_page': 12,
    },
    'top_200': {
        'url': 'https://crates.io/api/v1/crates?page={page}&per_page={per_page}&sort=downloads',
        'per_page': 50,
        'total_page': 4,
    },
    'top_500': {
        'url': 'https://crates.io/api/v1/crates?page={page}&per_page={per_page}&sort=downloads',
        'per_page': 50,
        'total_page': 10,
    },
}

class CratesSpider(scrapy.Spider):
    name = 'get-crates'
    crates = {}

    def __init__(self, category=None, *args, **kwargs):
        super(CratesSpider, self).__init__(*args, **kwargs)
        if category == None:
            self.category = 'bencher_rev_deps'
        else:
            self.category = category
        self.url = categ_attributes[self.category].get('url')
        self.per_page = categ_attributes[self.category].get('per_page')
        self.total_page = categ_attributes[self.category].get('total_page')


    def start_requests(self):
        url = self.url
        for page in range(self.total_page):
            yield Request.from_curl(
                "curl " + url.format(page=page+1, per_page=self.per_page),
                callback=self.parse)


    def parse(self, response):
        data = json.loads(response.body.decode('utf-8'))
        crates = {}

        if self.category == "bencher_rev_deps":
            if 'dependencies' not in data or 'versions' not in data:
                print("Error: invalid json")
                return None

            for dep in data['dependencies']:
                item = {'download': dep['downloads']}
                crates[dep['version_id']] = item
                print(dep['version_id'])

            for crate in data['versions']:
                item = {"name": crate['crate'], "version": crate['num'], "dl_path": crate['dl_path']}
                crates[crate['id']].update(item)
        else: 
            if 'crates' not in data:
                print("Error: invalid json")
                return None

            for crate in data['crates']:
                item = {"name": crate['name'], "version": crate['newest_version'], "dl_path": "/api/v1/crates/" + crate['name'] + "/" + crate['newest_version'] + "/download"}
                crates[crate['id']] = item

        self.crates.update(crates)
        self.download(crates)


    def download(self, crates):
        print("Start downloading!")
        newtopdir = "../" + self.category
        subprocess.run(["mkdir", "-p", newtopdir])
        for vid, crate in crates.items():
            subprocess.run(["wget", "https://crates.io" + crate['dl_path']])
            subprocess.run(["tar", "-C", newtopdir, "-xf", "download"])
            subprocess.run(["rm", "-f", "download"])

