<!--- <div align="center" id="top">
  <img src="./.github/app.gif" alt="Ncfig" />
</div> --->

<h1 align="center">NCFIG</h1>

<p align="center">
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/stig124/ncfig?color=56BEB8">

  <img alt="Github language count" src="https://img.shields.io/github/languages/count/stig124/ncfig?color=56BEB8">

  <img alt="Repository size" src="https://img.shields.io/github/repo-size/stig124/ncfig?color=56BEB8">

  <img alt="License" src="https://img.shields.io/github/license/stig124/ncfig?color=56BEB8">

  <!-- <img alt="Github issues" src="https://img.shields.io/github/issues/stig124/ncfig?color=56BEB8" /> -->

  <!-- <img alt="Github forks" src="https://img.shields.io/github/forks/stig124/ncfig?color=56BEB8" /> -->

  <!-- <img alt="Github stars" src="https://img.shields.io/github/stars/stig124/ncfig?color=56BEB8" /> -->
</p>

<!-- Status -->

<!-- <h4 align="center">
	🚧  Ncfig 🚀 Under construction...  🚧
</h4>

<hr> -->

<p align="center">
  <a href="#dart-about">About</a> &#xa0; | &#xa0;
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-starting">Starting</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a> &#xa0; | &#xa0;
  <a href="https://github.com/stig124" target="_blank">Author</a>
</p>

<br>

## :dart: About ##

Syncs NGINX reverse-proxy configuration with Cloudflare's API

## :sparkles: Features ##

:heavy_check_mark: Seamlessly sync your config file

:heavy_check_mark: Supports only API Token

:heavy_check_mark: Compatible with Linux and MacOS

:heavy_check_mark: Can delete and edit existing records when they leave the config file or when the IP change (soon...)

## :rocket: Technologies ##

The following tools were used in this project:

- [Python 3](https://www.python.org/)
- [Python-Cloudflare](https://github.com/cloudflare/python-cloudflare)
- [requests](https://pypi.org/project/requests/)
- [validators](https://pypi.org/project/validators/)

## :white_check_mark: Requirements ##

Before starting :checkered_flag:, you need to have [Python 3](https://www.python.org/), `pip` (`python3-pip` on `Debian/Ubuntu`) and `venv` (`python3-venv`) installed.

And generated an [API Token](https://developers.cloudflare.com/api/tokens/create) with at least the following permissions

- Zone:DNS Edit
- Zone:Zone Read

## :checkered_flag: Starting ##

Every command needs to be ran **as root**
For Rootless see the rootless paragraph

```bash
# Clone this project
git clone https://github.com/stig124/ncfig

# Access
cd ncfig

# Install dependencies
pip3 install pipenv && pipenv install

# Setup variables (Those commands needs to be ran each time program is to be executed)

export CF_API_KEY="API token between quotes"
export CONF="absolute path to nginx site config"

# Run the program (see usage for command switches)
python3 main.py

# If you want to rerun the program
# Go to the folder then
pipenv shell
# Configure variables as usual
python3 main.py

```


## :radio_button: Usage ##

```bash
python3 main.py (-r, --rootless) (-p, --proxy) (-y, --yes)
```

```bash
-p, --proxy : Enable Cloudflare's proxying (default: False)
-r, --rootless : Enables rootless mode (skip permission checking). (default: False)
-y, --yes : Runs the program non-interactively (default: False)
```

## Rootless operation ##

The toggle `-r` is not to be used on Linux if you've not made rootless installation, a great way to check that is if you have your site conf in `/etc/nginx` *(default folder)*, you don't need that and needs root permission to read

On a `brew` MacOS install, it is rootless by default, so you need to append `-r`

## :memo: License ##

This project is under GPL-3.0 license. For more details, see the [LICENSE](LICENSE) file.


Made with :heart: by <a href="https://github.com/stig124" target="_blank">Stig124</a>

&#xa0;

<a href="#top">Back to top</a>
