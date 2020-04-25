import scrapy
from scrapy import Request
import json
import re
import subprocess
count = 0

class CratesSpider(scrapy.Spider):
    name = 'crates'

    # Stopped checking githubs at page 6 (109 out of 118 is fine w me)
    def start_requests(self):
        urls = [
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=1&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=2&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=3&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=4&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=5&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=6&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=7&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=8&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=9&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=10&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=11&per_page=10',
            'https://crates.io/api/v1/crates/bencher/reverse_dependencies?page=12&per_page=10',
        ]
        for url in urls:
            yield Request.from_curl(
                "curl " + url + " -H 'authority: crates.io' -H 'user-agent: Mozilla/5.0 "
                + "(Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) "
                + "Chrome/79.0.3945.130 Safari/537.36' -H 'accept: */*' -H 'sec-fetch-site: "
                + "same-origin' -H 'sec-fetch-mode: cors' -H "
                + "'referer: https://crates.io/crates/bencher/reverse_dependencies' -H "
                + "'accept-encoding: gzip, deflate, br' -H 'accept-language: en-US,en;q=0.9' -H "
                + "'cookie: cargo_session=sJIiNcfM9yvCHoGNENQaO8JrPoTF1c7xuZ6xe/LTieY=' "
                + "--compressed", callback=self.parse)

    def parse(self, response):
        # Not necessary, just saving a backup of the data in response.body
        # just in case something goes wrong/to help with debugging

        page = "bencher_rev_deps"
        filename = 'crates-%s.html' % page
        with open(filename, 'wb') as f:
            f.write(response.body)

        #################################################################
        # Similar to last code block, except using the crate name to help
        # get to the github repository.
        #################################################################

        # Crate name pattern in response.body:
        # "crate":"<name>"

        matches = re.findall("\"crate\"\:\"[a-zA-Z0-9\-\_]+\"", 
                response.body.decode('utf-8'))
        paths = []
        for match in matches:
            _, name_str = re.split("\:", match)
            _, name, _ = re.split("\"", name_str)
            name_to_path = "https://crates.io/api/v1/crates/" + name
            paths.append(name_to_path)
        #global count
        for path in paths:
            #print("\n%s\n" % path)
            #count += 1
            yield Request.from_curl(
                "curl " + path + " -H 'authority: crates.io' -H 'user-agent: Mozilla/5.0 "
                + "(Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) "
                + "Chrome/79.0.3945.130 Safari/537.36' -H 'accept: */*' -H 'sec-fetch-site: "
                + "same-origin' -H 'sec-fetch-mode: cors' -H "
                + "'referer: https://crates.io/crates' -H "
                #+ "'referer: https://crates.io/crates/url' -H "
                + "'accept-encoding: gzip, deflate, br' -H 'accept-language: en-US,en;q=0.9' "
                + "-H 'cookie: cargo_session=sJIiNcfM9yvCHoGNENQaO8JrPoTF1c7xuZ6xe/LTieY=' "
                + "--compressed", callback=self.parse_for_github)

    # Following this link: https://crates.io/api/v1/crates/<crate_name>,
    # we can use this github repository pattern in the new response.body:
    #  "repository":"https://github.com/<unique_path>"

    def parse_for_github(self, response):
        matches = re.findall("\"repository\"\:\"https://github.com/[a-zA-Z0-9\/\-\_i\.]+\"",
                response.body.decode('utf-8'))
        repos = []
        for match in matches:
            _, repo_str = re.split("\:", match)
            _, repo, _ = re.split("\"", repo_str)
            if repo.endswith(".git"):
                fullrepo = repo
            else:
                fullrepo = repo + ".git"
            repos.append(fullrepo)
        global count
        for repo in repos:
            count += 1
            print("\n%s\n" % repo)
        print("\n%d\n" % count)

        # Using: "https://github.com/<unique_path>.git"
        # we can simply run `git clone` into the desired location. Next, 
        # we leverage the existing benchmarking infrastructure and 
        # automate running the benchmarks with and without bounds checks. 



        #################################################################
        # Problem with below code block: the `fullpath` that is extracted
        # does lead to the download of a binary, but since it is a binary 
        # gives no freedom to run the benchmarks (which are not typically 
        # included in binaries...). So, our last option is to automatically
        # follow links to github and go from there. 
        #################################################################

        # Crate download path pattern in response.body:
        #  "dl_path":"<path>"

#        matches = re.findall("\"dl_path\"\:\"[a-z0-9\-\_\/\.]+/download\"", 
#                response.body.decode('utf-8'))
#        paths = []
#        for match in matches:
#            _, path_str = re.split("\:", match)
#            _, path, _ = re.split("\"", path_str)
#            fullpath = "crates.io" + path
#            paths.append(fullpath)
#        global count
#        for path in paths:
#            print("\n%s\n" % path)
#            count += 1
#        print("\n%d\n" % count)

        #################################################################
        # Problem with below code: `cargo install` only installs binaries,
        # but most of the crates we want to use benchmarks from are _not_
        # binaries, so only 21 crates (out of a total of 117) are left as
        # candidates. Furthermore, 8 of those 21 would not successfully 
        # compile, and since I do not want to debug them, that leaves us 
        # with only 13 viable crates.
        #################################################################

        # Crate name pattern in response.body:
        # "crate":"<name>"
#
#        matches = re.findall("\"crate\"\:\"[a-z0-9\-\_]+\"", 
#                response.body.decode('utf-8'))
#        names = []
#        for match in matches:
#            _, name_str = re.split("\:", match)
#            _, name, _ = re.split("\"", name_str)
#            names.append(name)
#        global count
#        for name in names:
#            print("\n%s\n" % name)
#            count += 1
#            # (by default) installs binary into $HOME/.cargo/bin
#            output = subprocess.run(["cargo", "install", name])
#            print("exit code: %d\n" % output.returncode)
#        print("\n%d\n" % count)
