
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