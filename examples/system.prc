# system.prc — root system config

packages
	firefox
	neovim
	nano
	htop

services
	enable networking
	enable bluetooth

user
	name admin
	shell zsh

include networking.prc
include audio.prc
