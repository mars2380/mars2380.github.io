bootstrap:
	python3 -m venv new_env
	bash ./new_env/bin/activate || true
	pip list
	pip install --upgrade pip
	pip install -r requirements.txt

run:
	bash ./new_env/bin/activate || true
	python3 jobs_v2.1.py
# python3 jobs_v2.py > job.txt

run_test:
	python3 job_test.py 

git_push: git_pull
	@git status
	@git remote -v
	@echo "----------------------------"
	@git config user.name github-actions
	@git config user.email github-actions@github.com
	@git add .
	@git commit -m "Update index.html" || echo "No changes to commit"
	@echo "----------------------------"
	@git push


git_pull:
	@git pull
	@echo "----------------------------"

# git remote set-url --push origin https://${{ github.actor }}:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }} && \