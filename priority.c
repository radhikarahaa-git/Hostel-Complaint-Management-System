
#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[]) {

    if (argc != 3) {
        printf("Invalid input");
        return 1;
    }

    char category[30];
    char urgency[20];

    strcpy(category, argv[1]);
    strcpy(urgency, argv[2]);

    if (strcmp(urgency, "High") == 0) {

        if (strcmp(category, "Electricity") == 0 ||
            strcmp(category, "Water") == 0) {
            printf("Critical");
        }
        else {
            printf("High");
        }

    }
    else if (strcmp(urgency, "Medium") == 0) {

        if (strcmp(category, "Electricity") == 0 ||
            strcmp(category, "Water") == 0) {
            printf("High");
        }
        else {
            printf("Medium");
        }

    }
    else {
        printf("Low");
    }

    return 0;
}
