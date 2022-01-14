echo 'Generating documentation with pdoc...'
pdoc -t . --docformat google -o ./docs spectrumdevice
sed -i 's/index.html/contents.html/g' docs/spectrumdevice.html
sed -i 's/index.html/contents.html/g' docs/spectrumdevice/settings.html
mv docs/index.html docs/contents.html
sed -i 's/spectrumdevice.html/index.html/g' docs/contents.html
sed -i 's/spectrumdevice.html/index.html/g' docs/spectrumdevice/settings.html
mv docs/spectrumdevice.html docs/index.html
cp google322297713aa2081b.html docs/google322297713aa2081b.html