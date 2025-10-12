# summary the change by git diff and commit these change

1. 通过git diff读取当前的修改；
2. 通过是否存在`--full`判断总结内容：
   - 存在`--full`则总结所有git diff的内容；
   - 不存在`--full`总结除了`.gitignore`以外的所有文件；
3. 通过git add .和 git commit提交，并提交总结。