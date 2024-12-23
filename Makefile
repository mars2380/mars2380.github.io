bootstrap:
	python -m venv new_env
	bash ./new_env/bin/activate || true
	pip list
	pip install --upgrade pip
	pip install -r requirements.txt

run:
	python3 jobs_v2.py > job.json
	# python3 jobs_v2.py > job.txt

git_push:
	git pull && \
	git config user.name github-actions && \
	git config user.email github-actions@github.com && \
	git remote -v && \
	git add . && \
	git commit -m "Update index.html" && \
	echo "Push" && \
	git push

# git remote set-url --push origin https://${{ github.actor }}:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }} && \