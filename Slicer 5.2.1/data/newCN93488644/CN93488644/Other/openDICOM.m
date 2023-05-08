clear;

dirFolder = uigetdir();
imgFolder = dir(dirFolder);
imgFolder = imgFolder(~[imgFolder.isdir]);
numOfImages = length(imgFolder);
cd(dirFolder);

figure
for i = 1:numOfImages
    filename = imgFolder(i).name;
    disp(filename)
    info = dicominfo(filename);
    image = dicomread(info);

    name = append(num2str(i), '.png');
    dcmImagei = uint8(255 * mat2gray(image));
    imwrite(dcmImagei,name, 'png');
    
    imshow(image,[]);
    pause(0.5);
end